"""In-memory event stream with filtering and routing.

:class:`EventStream` is an ordered, immutable sequence of
:class:`~llm_schema.event.Event` objects with a fluent API for filtering and
routing to export backends.

Usage examples
--------------
**Build from a list**::

    stream = EventStream([event1, event2, event3])

**Filter**::

    errors = stream.filter(lambda e: "error" in e.payload)
    llm_trace = stream.filter_by_type("llm.trace.span.completed")

**Route to an exporter**::

    exporter = JSONLExporter("errors.jsonl")
    await stream.route(exporter, lambda e: e.event_type.startswith("llm.error"))

**Drain to an exporter (export all)**::

    await stream.drain(exporter)

**Load from a JSONL file**::

    stream = EventStream.from_file("audit.jsonl")

**Load from an asyncio.Queue**::

    stream = await EventStream.from_async_queue(queue)
"""

from __future__ import annotations

import asyncio
import queue as stdlib_queue
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Union,
    runtime_checkable,
)

from llm_schema.event import Event

__all__ = ["EventStream", "Exporter"]


# ---------------------------------------------------------------------------
# Exporter protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Exporter(Protocol):
    """Structural protocol for exporters accepted by :class:`EventStream`.

    Any object with an async ``export_batch`` method satisfies this protocol.
    All built-in exporters (:class:`~llm_schema.export.otlp.OTLPExporter`,
    :class:`~llm_schema.export.webhook.WebhookExporter`,
    :class:`~llm_schema.export.jsonl.JSONLExporter`) implement it.
    """

    async def export_batch(self, events: Sequence[Event]) -> Any:
        """Export a sequence of events."""
        ...


# ---------------------------------------------------------------------------
# EventStream
# ---------------------------------------------------------------------------


class EventStream:
    """An immutable, ordered sequence of :class:`~llm_schema.event.Event` objects.

    All methods that return a subset (``filter``, ``filter_by_type``,
    ``filter_by_tags``) return a **new** :class:`EventStream` without
    modifying the original.

    Args:
        events: Initial sequence of events.  Defaults to an empty stream.

    Example::

        stream = EventStream([event1, event2, event3])
        filtered = stream.filter_by_type("llm.trace.span.completed")
        await filtered.drain(exporter)
    """

    def __init__(self, events: Optional[Iterable[Event]] = None) -> None:
        self._events: List[Event] = list(events) if events is not None else []

    # ------------------------------------------------------------------
    # Class-method constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        *,
        encoding: str = "utf-8",
        skip_errors: bool = False,
    ) -> "EventStream":
        """Load events from a JSONL file.

        Each non-empty line is deserialized with
        :meth:`~llm_schema.event.Event.from_json`.  Lines that fail to
        deserialize are skipped when ``skip_errors=True``; by default they
        raise :class:`~llm_schema.exceptions.DeserializationError`.

        Args:
            path:        Path to a ``.jsonl`` file.
            encoding:    File encoding (default ``"utf-8"``).
            skip_errors: When ``True``, silently skip malformed lines instead
                         of raising.

        Returns:
            A new :class:`EventStream` with the loaded events.

        Raises:
            DeserializationError: On the first malformed line when
                ``skip_errors=False`` (default).
            OSError: If the file cannot be opened.
        """
        from llm_schema.exceptions import DeserializationError  # lazy import

        events: List[Event] = []
        with open(str(path), encoding=encoding) as fh:
            for lineno, raw_line in enumerate(fh, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    events.append(Event.from_json(line))
                except Exception as exc:
                    if skip_errors:
                        continue
                    raise DeserializationError(
                        reason=f"line {lineno}: {exc}",
                        source_hint=str(path),
                    ) from exc
        return cls(events)

    @classmethod
    def from_queue(
        cls,
        q: "stdlib_queue.Queue[Event]",
        *,
        sentinel: object = None,
    ) -> "EventStream":
        """Drain a synchronous :class:`queue.Queue` into an EventStream.

        Reads items from *q* until the queue is empty or a *sentinel* value is
        encountered.  Non-blocking: uses :meth:`queue.Queue.get_nowait` so this
        method returns immediately once the queue is drained.

        Args:
            q:        A :class:`queue.Queue` containing
                      :class:`~llm_schema.event.Event` objects.
            sentinel: Stop-value that signals end-of-stream.  The sentinel
                      itself is not added to the stream.  Defaults to ``None``.

        Returns:
            A new :class:`EventStream` with all events drained from the queue.
        """
        events: List[Event] = []
        while True:
            try:
                item = q.get_nowait()
            except stdlib_queue.Empty:
                break
            if item is sentinel:
                break
            events.append(item)
        return cls(events)

    @classmethod
    async def from_async_queue(
        cls,
        q: "asyncio.Queue[Event]",
        *,
        sentinel: object = None,
    ) -> "EventStream":
        """Drain an :class:`asyncio.Queue` into an EventStream.

        Awaits items from *q* until the *sentinel* value is received.  The
        sentinel itself is not added to the stream.

        Args:
            q:        An :class:`asyncio.Queue` containing
                      :class:`~llm_schema.event.Event` objects.
            sentinel: Stop-value (default ``None``).

        Returns:
            A new :class:`EventStream` with all events from the queue.
        """
        events: List[Event] = []
        while True:
            item = await q.get()
            if item is sentinel:
                break
            events.append(item)
        return cls(events)

    @classmethod
    async def from_async_iter(
        cls,
        aiter: "AsyncIterator[Event]",
    ) -> "EventStream":
        """Consume an async iterator into an EventStream.

        Args:
            aiter: Any :class:`~typing.AsyncIterator` of events.

        Returns:
            A new :class:`EventStream`.
        """
        events: List[Event] = []
        async for event in aiter:
            events.append(event)
        return cls(events)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter(
        self,
        predicate: Callable[[Event], bool],
    ) -> "EventStream":
        """Return a new stream containing only events for which *predicate*
        returns ``True``.

        Args:
            predicate: A callable that accepts an :class:`~llm_schema.event.Event`
                       and returns ``True`` to keep the event.

        Returns:
            New :class:`EventStream`.
        """
        return EventStream(e for e in self._events if predicate(e))

    def filter_by_type(self, *event_types: str) -> "EventStream":
        """Return a new stream containing only events whose ``event_type``
        matches one of the supplied strings (exact match).

        Args:
            *event_types: One or more event type strings.

        Returns:
            New :class:`EventStream`.
        """
        type_set = frozenset(event_types)
        return EventStream(e for e in self._events if e.event_type in type_set)

    def filter_by_tags(self, **tags: str) -> "EventStream":
        """Return a new stream keeping only events whose tags include **all**
        supplied key-value pairs.

        Args:
            **tags: Tag key=value pairs that must all be present.

        Returns:
            New :class:`EventStream`.
        """
        def _matches(event: Event) -> bool:
            if event.tags is None:
                return False
            tag_dict = event.tags.to_dict()
            return all(tag_dict.get(k) == v for k, v in tags.items())

        return EventStream(e for e in self._events if _matches(e))

    # ------------------------------------------------------------------
    # Routing & export
    # ------------------------------------------------------------------

    async def route(
        self,
        exporter: Exporter,
        predicate: Optional[Callable[[Event], bool]] = None,
    ) -> int:
        """Dispatch matching events to *exporter* as a single batch.

        Args:
            exporter:  Any object satisfying the :class:`Exporter` protocol
                       (has an async ``export_batch`` method).
            predicate: Optional filter.  When ``None`` all events are sent.

        Returns:
            Number of events dispatched.
        """
        if predicate is None:
            subset = self._events
        else:
            subset = [e for e in self._events if predicate(e)]

        if subset:
            await exporter.export_batch(subset)
        return len(subset)

    async def drain(self, exporter: Exporter) -> int:
        """Export all events in this stream to *exporter*.

        Equivalent to ``await stream.route(exporter)``.

        Args:
            exporter: Target exporter.

        Returns:
            Number of events exported.
        """
        return await self.route(exporter)

    # ------------------------------------------------------------------
    # Sequence protocol
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, index: Union[int, slice]) -> "Union[Event, EventStream]":
        result = self._events[index]
        if isinstance(index, slice):
            return EventStream(result)  # type: ignore[arg-type]
        return result  # type: ignore[return-value]

    def __repr__(self) -> str:
        return f"EventStream({len(self._events)} events)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventStream):
            return NotImplemented
        return self._events == other._events
