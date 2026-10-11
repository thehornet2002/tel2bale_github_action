#!/usr/bin/env python3
"""
Workflow rotation dispatcher.
Triggers the next workflow run via GitHub API to ensure continuous 24/7 execution.
"""
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("WORKFLOW_TOKEN") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    if not repo:
        print("[RETRIGGER] GITHUB_REPOSITORY not set. Running locally. Skipping dispatch.")
        return

    if not token:
        print("[RETRIGGER] No token available to dispatch workflow. Watchdog cron will trigger next run.")
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/bot.yml/dispatches"
    payload = json.dumps({"ref": "main"}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Tel2Bale-Workflow-Dispatcher",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 204):
                print("[RETRIGGER] Successfully dispatched next workflow run! Zero-downtime rotation initiated.")
                return
            print(f"[RETRIGGER] Dispatch returned status {resp.status}.")

    except urllib.error.HTTPError as e:
        status = e.code
        err_msg = e.read().decode("utf-8", errors="replace")
        if status in (401, 403, 404):
            print(f"[RETRIGGER] Notice: GitHub Actions default token cannot dispatch itself (HTTP {status}).")
            print("[RETRIGGER] The scheduled cron watchdog will automatically resume the bot within 30 minutes.")
            print("[RETRIGGER] (Tip: Add a Personal Access Token as 'WORKFLOW_TOKEN' in Secrets for instant zero-downtime handover).")
        else:
            print(f"[RETRIGGER] Dispatch warning: HTTP {status} - {err_msg}")

    except Exception as e:
        print(f"[RETRIGGER] Dispatch network error: {e}. Scheduled cron watchdog will resume execution.")


if __name__ == "__main__":
    main()
