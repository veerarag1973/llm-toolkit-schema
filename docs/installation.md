# Installation

## Requirements

- Python **3.9** or later
- No required third-party dependencies for core event creation

## Install from PyPI

```bash
pip install llm-toolkit-schema
```

## Optional extras

| Extra | Install command | What it enables |
|-------|-----------------|----------------|
| `jsonschema` | `pip install "llm-toolkit-schema[jsonschema]"` | `validate_event` with full JSON Schema validation |
| `http` | `pip install "llm-toolkit-schema[http]"` | `OTLPExporter` and `WebhookExporter` (stdlib transport; reserved for future `httpx` upgrade) |
| `pydantic` | `pip install "llm-toolkit-schema[pydantic]"` | `llm_toolkit_schema.models` — Pydantic v2 model layer, `model_json_schema()` |
| `otel` | `pip install "llm-toolkit-schema[otel]"` | `OTelBridgeExporter` — emits events through any configured `TracerProvider` (`opentelemetry-sdk>=1.24`) |
| `kafka` | `pip install "llm-toolkit-schema[kafka]"` | `EventStream.from_kafka()` via `kafka-python>=2.0` |
| `langchain` | `pip install "llm-toolkit-schema[langchain]"` | `LLMSchemaCallbackHandler` via `langchain-core>=0.2` |
| `llamaindex` | `pip install "llm-toolkit-schema[llamaindex]"` | `LLMSchemaEventHandler` via `llama-index-core>=0.10` |
| `datadog` | `pip install "llm-toolkit-schema[datadog]"` | `DatadogExporter` (stdlib transport; reserved for future `ddtrace` integration) |
| `all` | `pip install "llm-toolkit-schema[all]"` | All optional extras |

Install all optional extras at once:

```bash
pip install "llm-toolkit-schema[all]"
```

## Development installation

```bash
git clone https://github.com/llm-toolkit/llm-toolkit-schema.git
cd llm-toolkit-schema
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
```

This installs all development dependencies including pytest, ruff, mypy, and
all optional extras.

## Verify the installation

```python
import llm_toolkit_schema
print(llm_toolkit_schema.__version__)   # 1.1.2
print(llm_toolkit_schema.SCHEMA_VERSION)  # 1.0

from llm_toolkit_schema import Event, EventType
evt = Event(
    event_type=EventType.TRACE_SPAN_COMPLETED,
    source="smoke-test@1.0.0",
    payload={"ok": True},
)
evt.validate()
print("Installation OK")
```
