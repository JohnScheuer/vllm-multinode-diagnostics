"""Collect reproducibility and runtime provenance for benchmark nodes."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_NAMES = (
    "vllm",
    "ray",
    "torch",
    "transformers",
    "nvidia-ml-py",
)

MISSING_VALUES = {
    "",
    "N/A",
    "[N/A]",
    "NA",
    "NONE",
    "NOT SUPPORTED",
    "[NOT SUPPORTED]",
}


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def run_command(command: list[str]) -> dict[str, Any]:
    """Run a command without raising when it is unavailable or fails."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"command not found: {command[0]}",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": True,
            "returncode": None,
            "stdout": "",
            "stderr": "command timed out",
        }

    return {
        "available": True,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def package_version(name: str) -> str | None:
    """Return an installed Python distribution version if available."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def optional_float(value: str) -> float | None:
    """Parse an nvidia-smi numeric value, tolerating N/A-style output."""
    cleaned = value.strip()

    if cleaned.upper() in MISSING_VALUES:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def optional_int(value: str) -> int | None:
    """Parse an integer value, tolerating unsupported/malformed output."""
    cleaned = value.strip()

    if cleaned.upper() in MISSING_VALUES:
        return None

    try:
        return int(cleaned)
    except ValueError:
        return None


def collect_nvidia_smi() -> dict[str, Any]:
    """Collect NVIDIA driver and GPU information through nvidia-smi."""
    query = [
        "nvidia-smi",
        "--query-gpu="
        "index,name,uuid,memory.total,driver_version,"
        "pci.bus_id,pstate,temperature.gpu,power.limit",
        "--format=csv,noheader,nounits",
    ]

    result = run_command(query)

    if result["returncode"] != 0:
        return {
            "available": result["available"],
            "error": result["stderr"],
            "gpus": [],
        }

    gpus: list[dict[str, Any]] = []

    for line in result["stdout"].splitlines():
        if not line.strip():
            continue

        fields = [field.strip() for field in line.split(",")]

        if len(fields) != 9:
            gpus.append(
                {
                    "parse_error": "unexpected nvidia-smi field count",
                    "raw": line,
                }
            )
            continue

        (
            index,
            name,
            uuid,
            memory_total_mb,
            driver_version,
            pci_bus_id,
            pstate,
            temperature_c,
            power_limit_w,
        ) = fields

        gpus.append(
            {
                "index": optional_int(index),
                "name": name,
                "uuid": uuid,
                "memory_total_mb": optional_float(memory_total_mb),
                "driver_version": driver_version,
                "pci_bus_id": pci_bus_id,
                "pstate": pstate,
                "temperature_c": optional_float(temperature_c),
                "power_limit_w": optional_float(power_limit_w),
            }
        )

    return {
        "available": True,
        "error": None,
        "gpus": gpus,
    }


def collect_network_interfaces() -> list[str]:
    """Return network interface names visible under Linux sysfs."""
    net_path = Path("/sys/class/net")

    if not net_path.exists():
        return []

    return sorted(path.name for path in net_path.iterdir())


def collect_environment() -> dict[str, Any]:
    """Collect node-level environment provenance."""
    uname = platform.uname()

    return {
        "collected_at_utc": utc_now_iso(),
        "hostname": socket.gethostname(),
        "os": {
            "system": uname.system,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "platform": platform.platform(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "cpu": {
            "processor": uname.processor,
            "logical_cpu_count": os.cpu_count(),
        },
        "python_packages": {
            name: package_version(name)
            for name in PACKAGE_NAMES
        },
        "network_interfaces": collect_network_interfaces(),
        "nvidia": collect_nvidia_smi(),
        "commands": {
            "nvcc_version": run_command(["nvcc", "--version"]),
            "gcc_version": run_command(["gcc", "--version"]),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect node environment and GPU provenance."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of stdout only.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)

    payload = collect_environment()

    indent = 2 if args.pretty else None
    rendered = json.dumps(
        payload,
        indent=indent,
        sort_keys=True,
    )

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote environment manifest: {args.output}")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
