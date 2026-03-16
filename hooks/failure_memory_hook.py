#!/usr/bin/env python
import argparse
import subprocess
import sys
import json
from pathlib import Path

import httpx
import yaml


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def load_config(repo_root: Path) -> dict:
    cfg_path = repo_root / ".failure-memory" / "config" / "config.yml"
    if not cfg_path.exists():
        return {}
    return yaml.safe_load(cfg_path.read_text()) or {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook", required=True)
    parser.add_argument("--commit-msg-file")
    args = parser.parse_args()

    repo_root = Path(run(["git", "rev-parse", "--show-toplevel"]))
    cfg = load_config(repo_root)

    api = cfg.get("api", {})
    api_url = api.get("url", "http://localhost:8000")
    api_key = api.get("key", "")
    timeout = int(api.get("timeout", 30))

    analysis = cfg.get("analysis", {})
    use_llm = bool(analysis.get("use_llm", True))
    min_similarity = float(analysis.get("min_similarity", 0.6))
    max_results = int(analysis.get("max_results", 5))

    diff = run(["git", "diff", "--cached"]) if args.hook in ["pre-commit", "commit-msg"] else run(["git", "diff"])
    files = run(["git", "diff", "--cached", "--name-only"]).splitlines()

    commit_message = ""
    if args.commit_msg_file:
        commit_message = Path(args.commit_msg_file).read_text().strip()

    payload = {
        "commit_message": commit_message,
        "description": "",
        "diff": diff,
        "files_modified": files,
        "top_k": max_results,
        "use_llm": use_llm,
        "threshold": min_similarity,
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(f"{api_url}/api/v1/analyze-commit", json=payload, headers=headers)
            if resp.status_code != 200:
                print(f"Failure Memory check failed: {resp.status_code} {resp.text}")
                return 0
            data = resp.json()
            warning = data.get("warning")
            results = data.get("results", [])
            if warning or results:
                print("\n⚠️ FAILURE MEMORY WARNING ⚠️\n")
                if warning:
                    print(warning)
                for idx, r in enumerate(results, start=1):
                    print(f"{idx}. {r.get('title','Untitled')} (score: {r.get('score', 0):.2f})")
                print("\nReview similar failures before proceeding.\n")
    except Exception as exc:
        print(f"Failure Memory hook error: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
