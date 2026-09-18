# Multi-Node vLLM Telemetry & Automated Diagnostic Engine

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![vLLM](https://img.shields.io/badge/vLLM-Distributed-orange)

An empirical performance characterization suite and diagnostic engine for multi-node LLM serving (Ray + vLLM). Built for measuring inter-node communication bounds, pipeline bubbles, and tail latency tradeoffs in distributed inference.

## 🎯 Architecture Overview

When scaling LLM inference across separate compute nodes, performance transitions from **compute-bound** to **inter-node communication-bound**. This repository provides:

1. **Schema-Enforced Multi-Node Telemetry:** Structured JSON exports tracking Ray cluster handshakes, $p_{95}$ TTFT, $p_{95}$ TPOT, and throughput across Pipeline Parallel ($PP \ge 2$) execution.
2. **Communication-Cost Modeling:** Analytical $\alpha\text{--}\beta$ model decomposition separating network latency penalties from execution bubbles.
3. **Automated Diagnostic Reasoning Layer:** LLM-assisted diagnostic engine (powered by NVIDIA Nemotron via Nebius Token Factory) parsing raw metrics to generate evidence-backed performance post-mortems.

┌───────────────────────────┐ ┌───────────────────────────┐
│ Raw Multi-Node Telemetry │ ---> │ Empirical Diagnostic │ ---> │ Automated Nemotron │
│ (vLLM / Ray PP=2 Artifact)│ │ Engine (Alpha-Beta Model) │ │ Bottleneck Post-Mortem │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘


## 📂 Project Structure

vllm-multinode-diagnostics/
├── schema/ # Schema definition for multi-node JSON artifacts
│ └── benchmark_artifact_schema.json
├── artifacts/ # Raw multi-node benchmark runs (JSONs & logs)
│ └── raw_runs/
├── src/
│ └── multinode_diag/ # Core diagnostic reasoning engine & profiler
│ ├── init.py
│ ├── schema_val.py # Schema validator
│ └── alpha_beta.py # Analytical communication cost models
├── tests/ # Pytest validation suite
└── README.md


## 🚀 Quickstart

### 1. Validate Benchmark Artifacts
Ensure raw JSON exports adhere to the strict schema before diagnostic parsing:

python -m multinode_diag.schema_val --file artifacts/raw_runs/sample_run.json

2. Run Communication Cost Diagnostics

python -m multinode_diag.alpha_beta --file artifacts/raw_runs/sample_run.json

📊 Benchmark Schema Spec
Artifacts exported by multi-node execution workers must conform to schema/benchmark_artifact_schema.json, covering:

Node topology & GPU interconnect (TCP Ethernet, NVLink, PCIe PHB)
Concurrency sweeps (c∈[1,8,16,32]
Time-to-First-Token (p95  TTFT) & Time-per-Output-Token (p95 TPOT)
Inter-node rank handshake verification logs


📜 License
MIT License. Free for open-source research and distributed serving evaluation.