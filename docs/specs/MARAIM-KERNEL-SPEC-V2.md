# Maraim Kernel Specification v2.0

## Canonical Principle

**The Kernel is immutable. The DNA is mutable. Everything else is a RuntimeObject.**

Maraim v2 is not an agent framework and not a fixed workflow application. It is an AI Operating System kernel built around a small frozen core and an unlimited DNA Runtime Space.

## Non-Negotiable Rules

- No compiler.
- No JSON/YAML entity definitions.
- No generated registry.
- No duplicated definitions.
- No fixed list of DNA types inside the Kernel.
- No artificial limits on tokens, words, duration, tasks, agents, tool calls, models, or runtimes.
- Practical limits are only physical/runtime limits: CPU, RAM, disk, network, model provider, process limits, and safety policy.

## Kernel Core

The Kernel must remain small and stable. It hosts generic engines only:

1. Object Engine
2. Runtime Manager
3. Lifecycle Manager
4. Runtime Graph Engine
5. Discovery Engine
6. Scheduler Engine
7. Planner Engine
8. Execution Engine
9. Swarm Engine
10. Memory Engine
11. Knowledge Engine
12. Communication Engine
13. Resource Engine
14. Security / Policy Engine
15. Storage Engine
16. Diagnostics Engine
17. Evolution Engine

The Kernel does not know what an Agent, Team, Mission, Workflow, Model, Plugin, GGUF, ONNX, Dashboard, Connector, or Marketplace is. The Kernel only knows `RuntimeObject`.

## RuntimeObject Law

Everything in Maraim v2 is a RuntimeObject:

- Commander
- Mission
- Swarm
- Team
- Agent
- Skill
- Capability
- Tool
- Plugin
- Model
- GGUF model
- ONNX model
- Memory
- Knowledge
- Dashboard
- Connector
- Provider
- Service
- Any future type

A RuntimeObject has exactly one identity and exactly one runtime implementation.

## Identity

Every RuntimeObject must expose:

- `id`
- `namespace`
- `key`
- `version`
- `kind`
- `state`
- `capabilities`
- `metadata`

The unique identity is:

```text
namespace.key@version
```

The Kernel must reject duplicate active identities.

## Lifecycle

Every RuntimeObject follows the same lifecycle:

```text
Discover -> Validate -> Mount -> Connect -> Observe -> Scale -> Retire
```

Optional lifecycle actions:

```text
Create -> Clone -> Update -> Replace -> Enable -> Disable -> Reload -> Archive -> Delete -> Migrate
```

## Runtime Graph

The Kernel does not maintain lists such as `agents[]` or `plugins[]` as the primary structure. It maintains a graph.

Every RuntimeObject is a node. Every relationship is an edge.

Examples:

```text
Mission -> uses -> Agent
Agent -> owns -> Skill
Skill -> requires -> Capability
Capability -> bound_to -> Tool
Tool -> powered_by -> Model
Model -> reads -> Memory
Mission -> emits -> Artifact
```

The graph is dynamic and can change while the system is running.

## Swarm Engine

Swarm is not limited to agents.

Any RuntimeObject can become a Swarm:

- Agent Swarm
- Mission Swarm
- Tool Swarm
- Plugin Swarm
- Model Swarm
- Knowledge Swarm
- Memory Swarm
- Execution Swarm
- Validation Swarm
- Reasoning Swarm

The Swarm Engine supports:

```text
Split -> Spawn -> Dispatch -> Observe -> Retry -> Merge -> Validate -> Finish
```

## Scheduler and Planner

The Scheduler is not a simple FIFO queue. It runs a task graph:

```text
Mission -> Planner -> Task Graph -> Priority -> Dependencies -> Execution
```

## Execution Engine

Execution is not `run(task)`. It is:

```text
Plan -> Spawn -> Allocate -> Execute -> Observe -> Validate -> Recover -> Continue -> Merge -> Finish
```

## Memory Engine

Memory is not only working and long memory. It must support:

- Working memory
- Long memory
- Semantic memory
- Procedural memory
- Episodic memory
- Collective memory
- DNA memory

## Evolution Engine

Every mission writes execution telemetry:

- Performance
- Cost
- Latency
- Failures
- Quality
- Lessons learned
- Optimization opportunities

Evolution Engine uses that telemetry to improve future behavior without changing the Kernel.

## Capability Negotiation

RuntimeObjects should request capabilities, not concrete implementations.

Example request:

```text
need: text_generation, reasoning, embeddings
```

Resource Engine selects the best available RuntimeObject: GGUF, ONNX, Ollama, cloud API, plugin, local tool, or future model runtime.

## Final Architecture

```text
Small Kernel + Infinite DNA
```

Kernel Engines are few and stable. DNA Runtime Space is unlimited and mutable.
