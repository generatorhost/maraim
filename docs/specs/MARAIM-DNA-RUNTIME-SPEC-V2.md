# Maraim DNA Runtime Specification v2.0

## Definition

DNA is not data. DNA is not JSON. DNA is not YAML. DNA is not compiled.

DNA is a living runtime space. Every item inside DNA is an executable RuntimeObject.

## DNA Space

The DNA directory can contain any namespace. Examples:

```text
dna/
├── commanders/
├── missions/
├── swarms/
├── teams/
├── agents/
├── skills/
├── capabilities/
├── workflows/
├── plugins/
├── models/
├── connectors/
├── providers/
├── services/
├── memories/
├── schedulers/
├── planners/
├── analyzers/
├── executors/
├── reviewers/
├── generators/
├── interpreters/
├── validators/
├── optimizers/
├── reasoners/
├── orchestrators/
├── coordinators/
├── communicators/
├── knowledge/
├── vectorstores/
├── embeddings/
├── prompts/
├── policies/
├── rules/
├── permissions/
├── events/
├── tasks/
├── jobs/
├── artifacts/
├── projects/
├── organizations/
├── users/
├── tenants/
├── marketplaces/
├── freelance/
├── remote_work/
├── integrations/
├── apis/
├── mcp/
├── tools/
├── ui/
├── dashboards/
├── automation/
├── notifications/
├── monitoring/
├── security/
├── storage/
├── cache/
└── logs/
```

This list is illustrative, not fixed.

## Kernel Boundary

The Kernel never calls:

```python
load_agents()
load_teams()
load_models()
load_plugins()
```

The Kernel only calls:

```python
dna.discover()
dna.validate()
dna.mount_all(kernel)
```

## Universal Runtime Interface

Every DNA item must be represented by a RuntimeObject-compatible runtime.

Minimum contract:

```python
class DNARuntime:
    id = ""
    namespace = ""
    key = ""
    version = "1.0.0"
    kind = "runtime"

    def discover(self, kernel): ...
    def validate(self, kernel): ...
    def mount(self, kernel): ...
    def connect(self, kernel): ...
    def observe(self, kernel): ...
    def scale(self, kernel, target=None): ...
    def retire(self, kernel): ...
```

## Dynamic Management

DNA Runtime Manager must support:

- add_runtime
- remove_runtime
- update_runtime
- replace_runtime
- enable_runtime
- disable_runtime
- reload_runtime
- archive_runtime
- delete_runtime
- clone_runtime
- scale_runtime
- migrate_runtime
- validate_no_duplicate
- mount_all
- unmount

## No Duplication

A RuntimeObject is the definition, behavior, identity, and execution unit.

Disallowed:

```text
agent.py + agent.json
workflow.py + workflow.json
model.py + model_registry.json
plugin.py + generated_registry.py
```

Allowed:

```text
analyzer_runtime.py
project_acquisition_runtime.py
llama_gguf_runtime.py
embedding_onnx_runtime.py
```

## Model Runtime

Models are DNA RuntimeObjects. This includes:

- GGUF
- ONNX
- PyTorch
- TensorRT
- MLX
- OpenVINO
- llama.cpp
- Ollama
- OpenAI
- Anthropic
- Gemini
- Any future local or remote model provider

A model can be added, removed, updated, disabled, reloaded, or replaced like any other RuntimeObject.

## GGUF and ONNX

GGUF and ONNX are not special Kernel cases. They are Model RuntimeObjects.

Example identity:

```text
models.gguf.llama3_8b@1.0.0
models.onnx.embedding_arabic@1.0.0
```

The Kernel does not know the file format. Resource Engine selects a model based on declared capabilities.

## Capability Negotiation

A RuntimeObject requests a capability:

```text
text_generation
embedding
vision
reasoning
classification
reranking
speech_to_text
```

Resource Engine resolves that request to the best available RuntimeObject.

## Unlimited Expansion

Maraim does not impose artificial limits on number of runtimes, words, agents, tasks, missions, duration, models, or tool calls. Limits come only from available resources and runtime safety.
