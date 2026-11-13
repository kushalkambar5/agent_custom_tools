import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("BraveLauncher")

COMMON_BRAVE_PATHS = [
    os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
]

DEFAULT_DEBUG_PORT = 9222
DEDICATED_PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-ChatGPT-Automation\Profile")


def find_brave_executable() -> Optional[str]:
    """Find the path to the installed brave.exe executable on Windows."""
    for p in COMMON_BRAVE_PATHS:
        if os.path.isfile(p):
            return p

    try:
        which = subprocess.run(["where", "brave"], capture_output=True, text=True, check=False)
        if which.returncode == 0:
            lines = which.stdout.strip().splitlines()
            if lines and os.path.isfile(lines[0].strip()):
                return lines[0].strip()
    except Exception:
        pass

    return None


def is_port_listening(port: int = DEFAULT_DEBUG_PORT, timeout: float = 1.0) -> bool:
    """Check if Chrome DevTools Protocol is responding on the given port."""
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BraveLauncherCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return "webSocketDebuggerUrl" in data or "Browser" in data
    except Exception:
        return False
    return False


def is_brave_running() -> bool:
    """Check if any brave.exe processes are running on Windows."""
    try:
        output = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq brave.exe", "/NH"],
            capture_output=True,
            text=True,
            check=False
        )
        return "brave.exe" in output.stdout.lower()
    except Exception:
        return False


def wait_for_debug_port(port: int = DEFAULT_DEBUG_PORT, max_wait: float = 20.0) -> bool:
    """Wait until the remote debugging port responds."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if is_port_listening(port):
            return True
        time.sleep(0.5)
    return False


def launch_brave(
    port: int = DEFAULT_DEBUG_PORT,
    profile_mode: str = "auto",  # "auto", "dedicated", or "main"
    headless: bool = False,
    url: Optional[str] = "https://chatgpt.com"
) -> Tuple[bool, str]:
    """
    Ensure Brave is running with --remote-debugging-port.
    Never forcefully closes running Brave windows without user specification.
    """
    brave_path = find_brave_executable()
    if not brave_path:
        return False, "Could not locate brave.exe on this system. Please check your Brave installation."

    # 1. If debug port is already active, reuse it immediately
    if is_port_listening(port):
        return True, f"Brave remote debugging is already active on http://127.0.0.1:{port}"

    brave_active = is_brave_running()

    # 2. In 'auto' mode:
    # If Brave is already open for normal browsing, NEVER close it!
    # Instead, smoothly launch a dedicated automation profile side-by-side.
    if profile_mode == "auto":
        if brave_active:
            logger.info("Normal Brave is already open. Using dedicated profile to avoid closing your tabs...")
            profile_mode = "dedicated"
        else:
            profile_mode = "main"

    args = [brave_path, f"--remote-debugging-port={port}"]
    if headless:
        args.append("--headless=new")

    # 3. Launching
    if profile_mode == "dedicated":
        os.makedirs(DEDICATED_PROFILE_DIR, exist_ok=True)
        args.extend([
            f"--user-data-dir={DEDICATED_PROFILE_DIR}",
            "--no-first-run",
            "--no-default-browser-check"
        ])
        if url:
            args.append(url)
        logger.info(f"Launching Brave in dedicated profile (runs side-by-side, your work tabs remain open)...")
        subprocess.Popen(args)

    elif profile_mode == "main":
        if brave_active:
            msg = (
                f"[ERROR] Brave is currently running normally without port {port}.\n"
                "To avoid closing your open work tabs, use the dedicated profile instead:\n"
                "  python run.py --profile dedicated\n"
                "Or close Brave manually if you really want to use your main profile."
            )
            return False, msg

        if url:
            args.extend(["--restore-last-session", url])
        logger.info(f"Launching Brave (Main Profile) with port {port}...")
        subprocess.Popen(args)

    else:
        return False, f"Unknown profile mode: {profile_mode}"

    # 4. Wait for port to become active
    if wait_for_debug_port(port, max_wait=20.0):
        return True, f"Brave successfully started on http://127.0.0.1:{port} (mode: {profile_mode})"
    else:
        return False, f"Brave was launched, but port {port} did not respond within 20 seconds."


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    path = find_brave_executable()
    print(f"Brave Path: {path}")
    listening = is_port_listening(DEFAULT_DEBUG_PORT)
    print(f"Port {DEFAULT_DEBUG_PORT} Listening: {listening}")
    running = is_brave_running()
    print(f"Brave Running: {running}")
