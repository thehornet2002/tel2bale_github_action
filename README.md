# 🚀 TEL2BALE — GitHub Actions Edition (Serverless 24/7)

<div align="center">

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated_24%2F7-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Redis](https://img.shields.io/badge/Redis-Built--in_Service-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Security](https://img.shields.io/badge/Security-AES--256--GCM_Encrypted-success)](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Deploy and run the Telegram-to-Bale Bridge Bot completely free 24/7 using GitHub Actions. No VPS, server, or cloud hosting required!**

</div>

---

## 📌 Overview

This edition of **TEL2BALE** is specially engineered to run continuously 24/7 inside **GitHub Actions** runners.

Anyone can simply **Fork** this repository, add their bot credentials as **GitHub Secrets**, click **Run Workflow**, and the bot will start operating immediately!

### 💡 How It Works Under the Hood:
1. **5.5-Hour Rotation Cycle**: GitHub Actions enforces a strict 6-hour execution ceiling per job. The bot runs continuously for 330 minutes (5.5 hours), then performs an atomic graceful shutdown.
2. **Encrypted State Persistence (Zero-Knowledge)**: Before closing, the SQLite database (`bot.db`) and configuration are packed and encrypted using **AES-256-GCM** authenticated encryption, then committed to an isolated orphan branch (`storage`).
3. **Automatic Seamless Handover**: Upon finishing a cycle, the workflow automatically dispatches the next execution (or triggers via cron watchdog), restoring and decrypting the state without losing a single ticket, user, or configuration setting!
4. **Built-in Redis Service**: Runs an automated Redis container directly in GitHub Actions for lightning-fast user state and session processing.
5. **Anti-Collision Guard**: A built-in concurrency guard checks the GitHub API to ensure that two bot instances never run simultaneously, completely preventing Telegram `409 Conflict` errors.

---

## 🔒 Security Architecture (Safe for Public Forks)

Running a bot on GitHub Actions requires strict security, especially if your fork is **Public**:

- 🛡️ **Encrypted Database Storage**: Your `bot.db` contains user IDs, Bale tokens, and ticket history. Before being pushed to the remote repository, it is strongly encrypted with **AES-256-GCM** using PBKDF2 (100,000 iterations). Anyone viewing your public repository only sees an encrypted blob (`storage.enc`) that is mathematically impossible to decrypt without your secret key.
- 🔑 **Automatic Key Fallback**: If you do not specify a custom `STORAGE_KEY`, the encryption key is automatically derived from your `TEL_BOT_TOKEN`.
- 🗂 **Clean Git History**: The `main` branch code remains completely untouched. Database snapshots are stored on a separate orphan branch named `storage` with a single overwritten commit (`[skip ci]`).
- 🔐 **Zero Hardcoded Secrets**: All tokens and IDs are stored exclusively in your private GitHub Repository Secrets.

---

## 🚀 Quick Setup Guide (Step-by-Step for Forkers)

### Step 1: Fork This Repository
Click the **Fork** button at the top-right of this repository to create your own copy. Your repository can be **Public** or **Private**.

---

### Step 2: Configure Repository Secrets
In your forked repository, navigate to:
**Settings** ➔ **Secrets and variables** ➔ **Actions** ➔ **New repository secret**

Add the following secrets:

#### Required Secrets:
| Secret Name | Example Value | Description |
|---|---|---|
| `TEL_API_ID` | `12345678` | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `TEL_API_HASH` | `abcdef0123456789abcdef` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `TEL_BOT_TOKEN` | `123456789:ABCdefGhIjk...` | Telegram Bot Token from [@BotFather](https://t.me/BotFather) |
| `TEL_ADMIN_IDS` | `123456789,987654321` | Comma-separated Telegram numeric user IDs of administrators |

#### Optional Secrets:
| Secret Name | Default Value | Description |
|---|---|---|
| `STORAGE_KEY` | *(Auto-derived from Bot Token)* | Custom passphrase for AES-256-GCM database encryption |
| `WORKFLOW_TOKEN` | - | GitHub Personal Access Token (PAT with `workflow` scope) for instant zero-downtime rotation |
| `TEL_MAX_FILE_SIZE` | `20` | Maximum file size in MB for direct upload to Bale |
| `DONATION_LINK` | `https://daramet.com/Hornet2002` | Custom donation URL displayed on start keyboard |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | External Redis URL (leave empty to use built-in GHA Redis) |
| `SUPPORT_MESSAGE_LIMIT` | `5` | Maximum pending tickets allowed per user |
| `MAX_USERS` | `0` | Registration limit (0 = unlimited) |
| `MAX_ACTIVE_USERS` | `0` | Active Bale user limit (0 = unlimited) |
| `TEL_START_TXT` | - | Custom welcome message |
| `TEL_HELP_TXT` | - | Custom help message |

> 💡 **Tip regarding `WORKFLOW_TOKEN`**:
> - If you provide a Personal Access Token (`WORKFLOW_TOKEN`), the bot performs an **instant, zero-downtime handover** at the 5.5-hour mark.
> - If you do not provide one, the built-in 30-minute cron watchdog will automatically resume the bot with a brief pause.

---

### Step 3: Enable Workflow Permissions
To allow GitHub Actions to commit the encrypted database to the `storage` branch:

1. Go to your repository **Settings**.
2. On the left sidebar, click **Actions** ➔ **General**.
3. Scroll down to **Workflow permissions**.
4. Select **Read and write permissions**.
5. Check the box **Allow GitHub Actions to create and approve pull requests**.
6. Click **Save**.

---

### Step 4: Start the Bot
1. Click on the **Actions** tab at the top of your repository.
2. On the left sidebar, click **Tel2Bale Bot Runner**.
3. If workflows are disabled (GitHub disables workflows on newly forked repositories by default), click **I understand my workflows, go ahead and enable them**.
4. Click the **Run workflow** dropdown button on the right, and click **Run workflow**.

🎉 **Congratulations!** Your bot is now online, executing in the cloud 24/7 without requiring any server.

---

## ✨ Full Bot Feature List

All features from the flagship TEL2BALE engine are fully operational in this GitHub Actions edition:

- **All Media Types**: Forward photos, videos, voice notes, audio tracks, documents, stickers/animations, contacts, and locations directly to Bale messenger.
- **Large File S3 Cloud Storage**: Files larger than 20MB are automatically uploaded to Arvan Cloud S3 (or any S3 provider) with temporary presigned download links.
- **Advanced Ticket System**:
  - Custom topic categories (Normal or Anonymous).
  - User ticket history (`My Tickets`).
  - Full admin management interface with status filters (Pending, Answered, All) and in-bot replies.
- **Interactive Polls & Surveys**:
  - Admin survey creator with custom questions and choices.
  - User voting with live percentage and visual bar charts.
- **3-Way Security Captcha Challenge**:
  - Admin toggleable image captchas for Tickets, Polls, and File forwarding.
- **Admin Control Panel**:
  - Accessible anytime via `/admin` or `/panel`.
  - Whitelist mode enforcement.
  - Ban / Unban by Telegram ID or Bale ID.
  - Bandwidth quotas and user capacity controls.
  - Live database backup file delivery right inside Telegram.

---

## 🛠️ Management & Maintenance

### How to Stop the Bot
- Go to **Actions** ➔ **Tel2Bale Bot Runner** ➔ Click on the active running job ➔ Click **Cancel run**.
- To disable automated restarts, click the `...` menu on **Tel2Bale Bot Runner** and select **Disable workflow**.

### Viewing Live Logs
- Click on the active run in the **Actions** tab.
- Click on the **run-bot** job to view real-time log output and forwarding activity.

### How to Update Your Fork
To get the latest bug fixes and improvements:
1. Open your forked repository on GitHub.
2. Click the **Sync fork** button at the top of the repository and select **Update branch**.

---

## 📜 License

Distributed under the **[MIT License](LICENSE)**.
