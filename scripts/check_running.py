#!/usr/bin/env python3
"""
Concurrency check for GitHub Actions runner.
Prevents duplicate instances of the bot running concurrently to avoid Telegram 409 Conflict.
"""
import json
import os
import sys
import urllib.request


def set_output(name: str, value: str):
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output and os.path.exists(github_output):
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    print(f"[GUARD] Output set: {name}={value}")


def main():
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    current_run_id = os.getenv("GITHUB_RUN_ID")

    if not repo or not token or not current_run_id:
        print("[GUARD] Not running inside GitHub Actions or missing tokens. Allowing execution.")
        set_output("should_run", "true")
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/bot.yml/runs?status=in_progress"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Tel2Bale-Concurrency-Check",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        active_runs = data.get("workflow_runs", [])
        other_active_runs = [
            r for r in active_runs
            if str(r.get("id")) != str(current_run_id)
        ]

        if other_active_runs:
            other_id = other_active_runs[0].get("id")
            print(f"[GUARD] Another bot workflow run (#{other_id}) is currently in progress.")
            print("[GUARD] Skipping this run to prevent duplicate bot instances and Telegram 409 Conflict.")
            set_output("should_run", "false")
            return

        print("[GUARD] No other active bot runs detected. Safe to start.")
        set_output("should_run", "true")

    except Exception as e:
        print(f"[GUARD] Warning: Could not query GitHub Actions API: {e}. Proceeding with run.")
        set_output("should_run", "true")


if __name__ == "__main__":
    main()
