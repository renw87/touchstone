#!/usr/bin/env python3
"""Root runner for the A-share investment research Harness."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runner = Path(__file__).resolve().parent / "harness" / "runners" / "run_research.py"
    runpy.run_path(str(runner), run_name="__main__")
