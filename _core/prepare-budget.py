#!/usr/bin/env python3
"""Prepare an isolated Octomind config with a validated session cost threshold."""

import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def prepare(max_cost, config, env):
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", max_cost):
        raise ValueError("max_cost must be a positive USD decimal (for example 2.00)")
    amount = float(max_cost)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("max_cost must be finite and greater than zero")

    custom = config or env.get("OCTOMIND_CONFIG_PATH", "")
    if custom:
        source = Path(custom).resolve()
        if not source.is_file():
            raise ValueError("custom Octomind config must be an existing file")
    else:
        data = env.get("OCTOMIND_DATA_DIR")
        if not data:
            data = (str(Path(env.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "octomind")
                    if sys.platform == "win32" else
                    str(Path.home() / ".local/share/octomind"))
        source = Path(data).resolve() / "config/config.toml"

    directory = Path(tempfile.mkdtemp(prefix="octomind-budget-", dir=env["RUNNER_TEMP"]))
    try:
        # Octomind merges all sibling TOML files, not just the selected file.
        if source.parent.is_dir():
            for sibling in source.parent.glob("*.toml"):
                if sibling.is_file():
                    shutil.copy2(sibling, directory / sibling.name)
        selected = directory / source.name
        child_env = dict(env, OCTOMIND_CONFIG_PATH=str(selected))
        # Initialize defaults when needed and validate the copied config before overriding.
        subprocess.run(["octomind", "config", "--validate"], env=child_env, check=True,
                       stdout=sys.stderr)
        names = [p.name for p in directory.glob("*.toml")]
        # MCP override files load after ordinary files; sort last within that group.
        mcp_names = [name for name in names if name.startswith("mcp-")]
        overlay = directory / (max(mcp_names, default="mcp-action-budget.toml") + ".budget.toml")
        overlay.write_text(f"max_session_spending_threshold = {amount!r}\n", encoding="utf-8")
        subprocess.run(["octomind", "config", "--validate"], env=child_env, check=True,
                       stdout=sys.stderr)
        return selected
    except Exception:
        shutil.rmtree(directory)
        raise


if __name__ == "__main__":
    try:
        print(prepare(os.environ["INPUT_MAX_COST"], os.environ.get("INPUT_CONFIG", ""), os.environ))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
