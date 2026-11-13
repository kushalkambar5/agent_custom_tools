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


def kill_brave_processes() -> bool:
    """Terminate running brave.exe processes."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "brave.exe"], capture_output=True, check=False)
        time.sleep(2.0)
        return True
    except Exception as e:
        logger.error(f"Failed to kill Brave: {e}")
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
    profile_mode: str = "main",
    headless: bool = False,
    url: Optional[str] = "https://chatgpt.com",
    auto_restart: bool = False
) -> Tuple[bool, str]:
    """
    Ensure Brave is running with --remote-debugging-port on your main profile.
    Reuses existing open browser without closing it if port is already active.
    """
    brave_path = find_brave_executable()
    if not brave_path:
        return False, "Could not locate brave.exe on this system. Please check your Brave installation."

    # 1. If port is already active, we can connect directly without touching your open tabs!
    if is_port_listening(port):
        return True, f"Connected to your active Brave browser on port {port}."

    brave_active = is_brave_running()

    # 2. If Brave is already open without the port:
    if brave_active:
        if not auto_restart:
            print("\n" + "=" * 70)
            print(" [ACTION NEEDED] Your active Brave browser is not yet on debug port 9222.")
            print(" To connect to your open Brave window with your logged-in ChatGPT account:")
            print("   1. Close your running Brave window once.")
            print("   2. Reopen Brave by clicking your Taskbar icon (it now has port 9222 enabled).")
            print("   All your previous tabs and ChatGPT login will restore.")
            print("   From then on, you can run prompts anytime without ever closing Brave!")
            print("=" * 70)
            
            try:
                choice = input("\nWould you like this script to restart Brave now? (Y/n): ").strip().lower()
            except Exception:
                choice = "y"

            if choice == "n":
                return False, "Please reopen Brave from your Taskbar and run the script again."

        # Restart Brave once
        logger.info("Restarting Brave with your main profile on port 9222...")
        kill_brave_processes()

    # 3. Launch Brave with main profile and restore last session
    args = [brave_path, f"--remote-debugging-port={port}", "--restore-last-session"]
    if headless:
        args.append("--headless=new")
    if url:
        args.append(url)

    logger.info(f"Starting Brave on port {port}...")
    subprocess.Popen(args)

    if wait_for_debug_port(port, max_wait=20.0):
        return True, f"Brave ready on port {port}. Connected to your main profile."
    else:
        return False, f"Brave started, but port {port} did not respond within 20 seconds."


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    path = find_brave_executable()
    print(f"Brave Path: {path}")
    listening = is_port_listening(DEFAULT_DEBUG_PORT)
    print(f"Port {DEFAULT_DEBUG_PORT} Listening: {listening}")
    running = is_brave_running()
    print(f"Brave Running: {running}")
