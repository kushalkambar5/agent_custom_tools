import argparse
import sys
import os
import json
import logging
from pathlib import Path

from chatgpt_automator import ChatGPTAutomator

def print_banner():
    banner = r"""
  ==============================================================
             ChatGPT + Brave Browser Automation Tool
       Supports Text Output & DALL-E / 4o Image Generation
  ==============================================================
    """
    print(banner)


def display_result(result: dict):
    print("\n" + "=" * 60)
    print("                    CHATGPT RESPONSE")
    print("=" * 60)

    if not result.get("success"):
        print(f"\n[ERROR] {result.get('error')}\n")
        return

    text = result.get("text", "")
    if text:
        print("\n--- TEXT OUTPUT ---")
        print(text)

    images = result.get("images", [])
    if images:
        print(f"\n--- IMAGES GENERATED ({len(images)}) ---")
        for img in images:
            print(f"  [Image #{img['index']}]")
            if img.get("saved_path"):
                print(f"  Saved To : {img['saved_path']}")
            if img.get("url"):
                print(f"  Source   : {img['url'][:80]}...")
            if img.get("alt"):
                print(f"  Alt/Prompt : {img['alt']}")
            print()
    elif not text:
        print("\n(No text or images returned)")

    print("=" * 60 + "\n")


def interactive_mode(automator: ChatGPTAutomator):
    print("Entered Interactive Mode.")
    print("Type your prompt and press Enter. (Type 'exit', 'quit', or 'q' to stop)")
    print("Type '/new' to start a new chat conversation.")
    print("-" * 60)

    while True:
        try:
            prompt = input("\nChatGPT >> ").strip()
            if not prompt:
                continue

            if prompt.lower() in ["exit", "quit", "q"]:
                print("Exiting interactive mode...")
                break

            if prompt.lower() in ["/new", "/newchat", "/clear"]:
                automator.new_chat()
                print("Started a new chat session.")
                continue

            print("\nSending prompt to ChatGPT...")
            result = automator.send_prompt(prompt)
            display_result(result)

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {e}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Automate ChatGPT interactions in Brave Browser with text and image support."
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        help="Prompt to send to ChatGPT. If omitted, enters interactive mode."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="Brave remote debugging port (default: 9222)."
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["auto", "main", "dedicated"],
        default="auto",
        help="Profile mode: 'auto' (detect), 'main' (your regular profile), or 'dedicated' (runs side-by-side)."
    )
    parser.add_argument(
        "--new-chat",
        action="store_true",
        help="Start a new chat session before sending prompt."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save generated images and logs (default: ./outputs)."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Maximum seconds to wait for ChatGPT response (default: 180s)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON response to stdout."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging."
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")

    automator = ChatGPTAutomator(
        port=args.port,
        profile_mode=args.profile,
        output_dir=args.output_dir,
        timeout=args.timeout,
    )

    print("Initializing connection to Brave...")
    if not automator.start():
        print("[FAIL] Could not establish connection with Brave Browser.")
        sys.exit(1)

    try:
        if args.prompt:
            result = automator.send_prompt(args.prompt, new_chat=args.new_chat)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                display_result(result)
        else:
            interactive_mode(automator)
    finally:
        automator.stop()


if __name__ == "__main__":
    main()
