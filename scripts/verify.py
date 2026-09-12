"""Run the documented local checks and retain their real output and exit codes."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    evidence = root / ".local" / "verification"
    evidence.mkdir(parents=True, exist_ok=True)
    commands = [
        ("compose-config", ["docker", "compose", "config", "--quiet"]),
        (
            "startup",
            [
                "docker",
                "compose",
                "up",
                "--build",
                "-d",
                "--wait",
                "--wait-timeout",
                "180",
            ],
        ),
        (
            "django-check",
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "python",
                "manage.py",
                "check",
            ],
        ),
        (
            "migration-drift",
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "python",
                "manage.py",
                "makemigrations",
                "--check",
                "--dry-run",
            ],
        ),
        ("backend-tests", ["docker", "compose", "exec", "-T", "backend", "pytest"]),
        ("lint", ["docker", "compose", "exec", "-T", "backend", "ruff", "check", "."]),
        (
            "format",
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "ruff",
                "format",
                "--check",
                ".",
            ],
        ),
        (
            "http-smoke",
            [
                sys.executable,
                "scripts/smoke.py",
                sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173",
            ],
        ),
    ]
    results = []
    for name, command in commands:
        print(f"Running {name}...", flush=True)
        with (evidence / f"{name}.log").open("w", encoding="utf-8") as output:
            result = subprocess.run(
                command, cwd=root, stdout=output, stderr=subprocess.STDOUT, check=False
            )
        results.append({"name": name, "command": command, "exit_code": result.returncode})
        (evidence / "results.json").write_text(
            json.dumps(
                {
                    "executed_at": datetime.now(UTC).isoformat(),
                    "checks": results,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode:
            print((evidence / f"{name}.log").read_text(encoding="utf-8"))
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
