#!/usr/bin/env python3
"""
Validates required bot credentials before starting execution.
Provides user-friendly error messages if repository secrets are missing.
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    api_id = os.getenv("TEL_API_ID", "").strip()
    api_hash = os.getenv("TEL_API_HASH", "").strip()
    bot_token = os.getenv("TEL_BOT_TOKEN", "").strip()
    admin_ids = os.getenv("TEL_ADMIN_IDS", "").strip()

    missing = []
    if not api_id or api_id == "0":
        missing.append("TEL_API_ID")
    if not api_hash:
        missing.append("TEL_API_HASH")
    if not bot_token:
        missing.append("TEL_BOT_TOKEN")
    if not admin_ids:
        missing.append("TEL_ADMIN_IDS")

    if missing:
        print("\n" + "=" * 72)
        print("❌ CONFIGURATION ERROR: Missing Required GitHub Repository Secrets!")
        print("=" * 72)
        print("The following required secrets are missing or empty in your repository:")
        for m in missing:
            print(f"  • {m}")
        print("\n👉 How to add them:")
        print("1. In your GitHub repository, click 'Settings' tab.")
        print("2. On the left menu, click 'Secrets and variables' -> 'Actions'.")
        print("3. Click the green 'New repository secret' button.")
        print("4. Add each missing secret with its corresponding value.")
        print("5. Return to the 'Actions' tab and re-run the workflow.")
        print("=" * 72 + "\n")
        sys.exit(1)

    print("[CONFIG] All required credentials verified successfully.")


if __name__ == "__main__":
    main()
