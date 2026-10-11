#!/usr/bin/env python3
"""
Storage Manager for GitHub Actions.
Safely encrypts and persists bot state (SQLite bot.db & settings) to an orphan git branch 'storage'
using AES-256-GCM encryption, preventing exposure of user tokens and IDs even in public repositories.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

HEADER = b"T2B_GCM_V1"


def get_passphrase() -> str:
    passphrase = (
        os.getenv("STORAGE_KEY")
        or os.getenv("TEL_BOT_TOKEN")
        or os.getenv("TEL_API_HASH")
        or ""
    ).strip()
    if not passphrase:
        raise ValueError(
            "No encryption key found. Set STORAGE_KEY or TEL_BOT_TOKEN in GitHub repository Secrets."
        )
    return passphrase


def encrypt_data(data: bytes, passphrase: str) -> bytes:
    if HAS_CRYPTOGRAPHY:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = kdf.derive(passphrase.encode("utf-8"))
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return HEADER + salt + nonce + ciphertext
    elif shutil.which("openssl"):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f_in, tempfile.NamedTemporaryFile("wb", delete=False) as f_out:
            f_in.write(data)
            f_in_name = f_in.name
            f_out_name = f_out.name
        try:
            subprocess.run(
                ["openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-in", f_in_name, "-out", f_out_name, "-k", passphrase],
                check=True,
                capture_output=True,
            )
            with open(f_out_name, "rb") as f:
                return f.read()
        finally:
            for p in (f_in_name, f_out_name):
                if os.path.exists(p):
                    os.remove(p)
    else:
        raise RuntimeError("Neither 'cryptography' package nor 'openssl' CLI is available for encryption.")


def decrypt_data(payload: bytes, passphrase: str) -> bytes:
    if payload.startswith(HEADER):
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("'cryptography' package required to decrypt AES-GCM archive.")
        salt = payload[len(HEADER):len(HEADER) + 16]
        nonce = payload[len(HEADER) + 16:len(HEADER) + 28]
        ciphertext = payload[len(HEADER) + 28:]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = kdf.derive(passphrase.encode("utf-8"))
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    elif shutil.which("openssl"):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f_in, tempfile.NamedTemporaryFile("wb", delete=False) as f_out:
            f_in.write(payload)
            f_in_name = f_in.name
            f_out_name = f_out.name
        try:
            subprocess.run(
                ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", f_in_name, "-out", f_out_name, "-k", passphrase],
                check=True,
                capture_output=True,
            )
            with open(f_out_name, "rb") as f:
                return f.read()
        finally:
            for p in (f_in_name, f_out_name):
                if os.path.exists(p):
                    os.remove(p)
    else:
        raise RuntimeError("Cannot decrypt archive: payload header unrecognized and OpenSSL is not available.")


def restore():
    print("[STORAGE] Restoring persistent bot state...")
    try:
        passphrase = get_passphrase()
    except ValueError as e:
        print(f"[STORAGE] Warning: {e}. Skipping restore.")
        return

    encrypted_bytes = None

    # Check if storage.enc exists locally first
    if os.path.exists("storage.enc"):
        print("[STORAGE] Found local storage.enc file. Restoring from it...")
        with open("storage.enc", "rb") as f:
            encrypted_bytes = f.read()
    else:
        # Check if 'storage' branch exists on origin
        check_branch = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", "storage"],
            capture_output=True,
            text=True,
        )
        if not check_branch.stdout.strip():
            print("[STORAGE] No 'storage' branch found on remote repository. Starting with fresh state.")
            return

        # Fetch storage branch object
        fetch_res = subprocess.run(
            ["git", "fetch", "origin", "storage:refs/remotes/origin/storage"],
            capture_output=True,
            text=True,
        )
        if fetch_res.returncode != 0:
            print(f"[STORAGE] Warning: Failed to fetch storage branch: {fetch_res.stderr}. Starting fresh.")
            return

        # Extract storage.enc from origin/storage
        show_res = subprocess.run(
            ["git", "show", "origin/storage:storage.enc"],
            capture_output=True,
        )
        if show_res.returncode != 0 or not show_res.stdout:
            print("[STORAGE] No 'storage.enc' file found on storage branch. Starting fresh.")
            return

        encrypted_bytes = show_res.stdout

    try:
        decrypted_tar = decrypt_data(encrypted_bytes, passphrase)
    except Exception as e:
        print(f"[STORAGE] ERROR: Failed to decrypt state archive ({e}).")
        print("[STORAGE] Check that STORAGE_KEY or TEL_BOT_TOKEN matches the one used to encrypt.")
        return

    # Unpack tar archive
    tar_stream = io.BytesIO(decrypted_tar)
    restored_files = []
    with tarfile.open(fileobj=tar_stream, mode="r:gz") as tar:
        for member in tar.getmembers():
            if hasattr(tarfile, "data_filter"):
                tar.extract(member, path=".", filter="data")
            else:
                tar.extract(member, path=".")
            restored_files.append(member.name)

    print(f"[STORAGE] State successfully restored! Restored files: {', '.join(restored_files)}")


def backup():
    print("[STORAGE] Backing up and encrypting persistent state...")
    if not os.path.exists("bot.db"):
        print("[STORAGE] No 'bot.db' file found to back up. Skipping.")
        return

    try:
        passphrase = get_passphrase()
    except ValueError as e:
        print(f"[STORAGE] Warning: {e}. Skipping backup.")
        return

    # Pack files into tar.gz
    tar_stream = io.BytesIO()
    files_to_pack = ["bot.db"]
    if os.path.exists(".env"):
        files_to_pack.append(".env")

    with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
        for f in files_to_pack:
            tar.add(f, arcname=f)

    tar_bytes = tar_stream.getvalue()
    encrypted_bytes = encrypt_data(tar_bytes, passphrase)

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not token or not repo:
        print("[STORAGE] No GITHUB_TOKEN or GITHUB_REPOSITORY environment variable. Saving locally as 'storage.enc'.")
        with open("storage.enc", "wb") as f:
            f.write(encrypted_bytes)
        return

    remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"

    # Push to orphan 'storage' branch using an isolated temporary git directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "checkout", "--orphan", "storage"], cwd=tmp_dir, check=True, capture_output=True)

        with open(os.path.join(tmp_dir, "storage.enc"), "wb") as f:
            f.write(encrypted_bytes)

        readme_text = (
            "# Tel2Bale Persistent Storage\n\n"
            "This orphan branch stores encrypted bot state (`storage.enc`).\n"
            "The archive is encrypted with AES-256-GCM. Do not edit manually.\n"
        )
        with open(os.path.join(tmp_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_text)

        subprocess.run(["git", "add", "storage.enc", "README.md"], cwd=tmp_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore(storage): automated encrypted state update [skip ci]"],
            cwd=tmp_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=tmp_dir, check=True)

        push_res = subprocess.run(
            ["git", "push", "--force", "origin", "storage"],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
        )
        if push_res.returncode == 0:
            print("[STORAGE] State successfully encrypted and pushed to 'storage' branch.")
        else:
            print(f"[STORAGE] Warning: Failed to push to 'storage' branch: {push_res.stderr}")
            if "403" in push_res.stderr or "Permission" in push_res.stderr or "denied" in push_res.stderr:
                print("\n" + "=" * 70)
                print("⚠️  PERMISSION ACTION REQUIRED:")
                print("GitHub Actions does not have write permissions to your repository.")
                print("To fix this and enable automatic state persistence:")
                print("1. Go to your repository Settings -> Actions -> General.")
                print("2. Under 'Workflow permissions', select 'Read and write permissions'.")
                print("3. Check 'Allow GitHub Actions to create and approve pull requests'.")
                print("4. Click 'Save'.")
                print("=" * 70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("restore", "backup"):
        print("Usage: python storage_manager.py [restore|backup]")
        sys.exit(1)

    if sys.argv[1] == "restore":
        restore()
    elif sys.argv[1] == "backup":
        backup()
