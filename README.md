# Multi-Node vLLM Telemetry & Automated Diagnostic Engine

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![vLLM](https://img.shields.io/badge/vLLM-Distributed-orange)

A reproducible telemetry, benchmarking, and diagnostic framework for
multi-node vLLM inference.

The project is being developed around distributed vLLM deployments using
Ray, with an initial two-node pipeline-parallel baseline and a future
NVIDIA Nemotron diagnostic reasoning layer.

## Architecture

The intended data flow is:

```text
vLLM / Ray benchmark
        |
        v
raw benchmark artifact
        |
        v
schema validation
        |
        v
empirical diagnostics
        |
        v
Nemotron-assisted post-mortem
```

The benchmark and diagnostics layers are intentionally separated from any
specific vLLM compatibility distribution.

## Initial Experimental Topology

The first planned distributed baseline is:

```text
Node 0                      Node 1
1 x NVIDIA T4              1 x NVIDIA T4
Ray head                   Ray worker
PP rank 0                  PP rank 1
      \                    /
       ---- TCP network ----

TP = 1
PP = 2
DP = 1
```

The planned initial concurrency matrix is:

```text
[1, 8, 16, 32]
```

with controlled input and output token counts.

## Repository Structure

```text
vllm-multinode-diagnostics/
├── artifacts/
│   ├── examples/
│   └── raw_runs/
├── schema/
│   └── benchmark_artifact_schema.json
├── src/
│   └── multinode_diag/
│       ├── __init__.py
│       ├── collect_env.py
│       └── schema_val.py
├── tests/
├── LICENSE
├── README.md
└── pyproject.toml
```

## Python

Python 3.11 or newer is required.

A virtual environment is not required.

For development from a source checkout:

```bash
PYTHONPATH=src python3.11 -m multinode_diag.collect_env --pretty
```

## Validate an Artifact

```bash
PYTHONPATH=src python3.11 -m multinode_diag.schema_val \
  --file artifacts/examples/aws-g4dn-pp2-sample.json
```

A valid artifact prints:

```text
VALID: artifacts/examples/aws-g4dn-pp2-sample.json
```

## Collect Node Provenance

The environment collector records:

- operating system and kernel
- Python runtime
- selected Python package versions
- network interfaces
- NVIDIA GPU information when available
- NVIDIA driver metadata
- CUDA toolkit information when `nvcc` is available
- GCC information

Unsupported NVIDIA telemetry values such as `N/A` are represented as JSON
`null` rather than causing collection to fail.

Run:

```bash
PYTHONPATH=src python3.11 -m multinode_diag.collect_env --pretty
```

Write a manifest to disk:

```bash
PYTHONPATH=src python3.11 -m multinode_diag.collect_env \
  --pretty \
  --output node-env.json
```

Review machine-specific manifests before committing them.

## Benchmark Artifact Schema

The schema separates:

- execution platform and framework provenance
- node and GPU topology
- inter-node network topology
- model identity and revision
- tensor, pipeline, and data parallel configuration
- workload definition
- latency and throughput measurements
- distributed rank handshake state

Inter-node networking is intentionally modeled separately from GPU/device
interconnect concepts.

## Testing

Install the development requirements into the active Python 3.11 user
environment as needed:

```bash
python3.11 -m pip install --user pytest jsonschema
```

Run:

```bash
PYTHONPATH=src python3.11 -m pytest -q
```

The current unit tests do not require Ray, vLLM, CUDA, or an NVIDIA GPU.

## Roadmap

Planned follow-up work includes:

1. Ray two-node cluster bootstrap and verification.
2. Upstream vLLM pipeline-parallel launch support.
3. Controlled concurrency benchmark execution.
4. Per-node GPU and host telemetry.
5. Normalized benchmark artifact generation.
6. Communication-cost analysis.
7. NVIDIA Nemotron / Nebius diagnostic reasoning.

## License

MIT License.
