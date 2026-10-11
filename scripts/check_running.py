#!/usr/bin/env python3
"""
Concurrency guard for Tel2Bale GitHub Actions Runner.
Prevents duplicate instances of the bot running concurrently to eliminate Telegram 409 Conflict.
Supports force restart to cancel stale runs when requested.
"""
import json
import os
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def set_output(name: str, value: str):
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output and os.path.exists(github_output):
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    print(f"[GUARD] Output set: {name}={value}")


def cancel_run(repo: str, token: str, run_id: int):
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/cancel"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Tel2Bale-Guard",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[GUARD] Cancelled older run #{run_id} (Status: {resp.status})")
    except Exception as e:
        print(f"[GUARD] Could not cancel run #{run_id}: {e}")


def main():
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    current_run_id = os.getenv("GITHUB_RUN_ID")
    force_restart = os.getenv("FORCE_RESTART", "false").lower() == "true"

    if not repo or not token or not current_run_id:
        print("[GUARD] Running outside GitHub Actions or missing tokens. Allowing execution.")
        set_output("should_run", "true")
        return

    # Query active runs for this repository
    url = f"https://api.github.com/repos/{repo}/actions/runs?status=in_progress"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Tel2Bale-Guard",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        active_runs = data.get("workflow_runs", [])
        other_active_runs = [
            r for r in active_runs
            if str(r.get("id")) != str(current_run_id)
            and "bot" in str(r.get("path", "")).lower() or "tel2bale" in str(r.get("name", "")).lower()
        ]

        if other_active_runs:
            if force_restart:
                print("[GUARD] Force restart requested. Cancelling older active runs...")
                for r in other_active_runs:
                    cancel_run(repo, token, r.get("id"))
                set_output("should_run", "true")
                return

            other_id = other_active_runs[0].get("id")
            print(f"[GUARD] Another bot workflow run (#{other_id}) is currently in progress.")
            print("[GUARD] Skipping this run to prevent duplicate bot instances and Telegram 409 Conflict.")
            print("[GUARD] (To override and restart, run workflow with 'Force Restart' enabled).")
            set_output("should_run", "false")
            return

        print("[GUARD] No other active bot runs detected. Safe to start.")
        set_output("should_run", "true")

    except Exception as e:
        print(f"[GUARD] Warning: Could not query GitHub Actions API: {e}. Proceeding with run.")
        set_output("should_run", "true")


if __name__ == "__main__":
    main()
