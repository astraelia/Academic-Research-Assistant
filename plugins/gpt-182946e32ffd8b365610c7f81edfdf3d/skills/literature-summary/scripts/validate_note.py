#!/usr/bin/env python3
"""Compatibility entrypoint; validation logic is maintained at plugin/scripts/validate_note.py."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[3] / "scripts" / "validate_note.py"), run_name="__main__")
