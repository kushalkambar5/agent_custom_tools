import os
import sys
import time
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, BrowserContext, ElementHandle, TimeoutError as PlaywrightTimeoutError

import brave_launcher

logger = logging.getLogger("ChatGPTAutomator")


class ChatGPTAutomator:
    """
    Automates ChatGPT in Brave Browser via Chrome DevTools Protocol (CDP).
    Supports prompt input, text output retrieval, and DALL-E / 4o image generation download.
    Runs side-by-side with your existing Brave browser without closing your tabs.
    """

    def __init__(
        self,
        port: int = 9222,
        profile_mode: str = "auto",  # 'auto', 'dedicated', or 'main'
        output_dir: Optional[str] = None,
        timeout: int = 180,
    ):
        self.port = port
        self.profile_mode = profile_mode
        self.timeout = timeout
        self.output_dir = Path(output_dir or Path(__file__).parent / "outputs")
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = None
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> bool:
        """Connect to Brave or launch it if necessary."""
        logger.info(f"Checking for Brave remote debugging on port {self.port}...")

        if not brave_launcher.is_port_listening(self.port):
            logger.info(f"Port {self.port} is not listening. Preparing to launch Brave...")

            success, msg = brave_launcher.launch_brave(
                port=self.port,
                profile_mode=self.profile_mode,
                url="https://chatgpt.com"
            )
            print(msg)
            if not success:
                return False

        # Connect Playwright over CDP
        self._playwright = sync_playwright().start()
        try:
            logger.info(f"Connecting to Brave at http://127.0.0.1:{self.port}...")
            self._browser = self._playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{self.port}")
            if not self._browser.contexts:
                self._context = self._browser.new_context()
            else:
                self._context = self._browser.contexts[0]
            
            self._setup_chatgpt_page()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Brave over CDP: {e}")
            self.stop()
            return False

    def _setup_chatgpt_page(self):
        """Find an existing ChatGPT tab or open a new one."""
        chatgpt_page = None
        for page in self._context.pages:
            if "chatgpt.com" in page.url:
                chatgpt_page = page
                break

        if chatgpt_page:
            logger.info("Found existing ChatGPT tab. Reusing it.")
            self._page = chatgpt_page
            self._page.bring_to_front()
        else:
            logger.info("Opening new tab with https://chatgpt.com...")
            self._page = self._context.new_page()
            self._page.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=60000)

        self._ensure_ready()

    def _ensure_ready(self):
        """Wait until ChatGPT prompt input is visible and ready."""
        editor_selector = 'div[contenteditable="true"], div.ProseMirror, div[aria-label="Ask ChatGPT"], #prompt-textarea'
        login_btn_selector = 'button[data-testid="login-button"], a[data-testid="login-button"], a[href*="/auth/login"]'

        # Quick check if already ready
        try:
            if self._page.locator(editor_selector).first.is_visible(timeout=3000):
                print("✓ ChatGPT editor ready.")
                return
        except Exception:
            pass

        # Check if login is needed (e.g. first run of dedicated profile)
        try:
            if self._page.locator(login_btn_selector).first.is_visible(timeout=2000):
                print("\n" + "=" * 65)
                print(" [ACTION REQUIRED] Please log into ChatGPT in the opened Brave window.")
                print(" Your login session will be permanently saved for all future runs.")
                print(" Waiting for login to complete...")
                print("=" * 65 + "\n")
        except Exception:
            pass

        print("Waiting for ChatGPT editor to become ready...")
        start_wait = time.time()
        while time.time() - start_wait < 300:
            try:
                el = self._page.locator(editor_selector).first
                if el.is_visible(timeout=2000):
                    print("✓ ChatGPT editor ready.\n")
                    return
            except Exception:
                pass
            time.sleep(2)

        logger.warning("Timed out waiting for editor. Continuing anyway.")

    def new_chat(self):
        """Start a fresh chat conversation."""
        if not self._page:
            return
        logger.info("Starting a new chat...")
        self._page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        time.sleep(2)
        self._ensure_ready()

    def send_prompt(self, prompt: str, new_chat: bool = False) -> Dict[str, Any]:
        """
        Send a prompt to ChatGPT and return the generated text and images.
        """
        if not self._page:
            return {"success": False, "error": "Browser page is not initialized."}

        if new_chat:
            self.new_chat()

        self._page.bring_to_front()

        # 1. Locate editor
        editor_selector = 'div[contenteditable="true"], div.ProseMirror, div[aria-label="Ask ChatGPT"], #prompt-textarea'
        try:
            editor = self._page.locator(editor_selector).first
            editor.wait_for(state="visible", timeout=20000)
            editor.click()
            time.sleep(0.3)
        except Exception as e:
            return {"success": False, "error": f"Could not find prompt editor: {e}"}

        # 2. Type prompt
        logger.info(f"Submitting prompt: {prompt[:80]}...")
        try:
            editor.fill(prompt)
        except Exception:
            self._page.keyboard.type(prompt)

        time.sleep(0.5)

        # 3. Submit prompt
        send_btn = self._page.locator('button[aria-label="Send"], button[data-testid="send-button"]').first
        if send_btn.is_visible() and send_btn.is_enabled():
            send_btn.click()
        else:
            self._page.keyboard.press("Enter")

        logger.info("Prompt submitted. Waiting for response/image generation...")

        # 4. Wait for completion
        return self._wait_for_completion()

    def _wait_for_completion(self) -> Dict[str, Any]:
        """Wait for text streaming or image rendering to complete."""
        poll_start = time.time()
        saw_stop_button = False

        while time.time() - poll_start < self.timeout:
            time.sleep(1.5)
            elapsed = int(time.time() - poll_start)

            status = self._page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button')).map(b => (b.getAttribute('aria-label') || '').toLowerCase());
                const hasStop = btns.some(l => l.includes('stop'));
                
                const imgs = Array.from(document.querySelectorAll('img')).map(i => ({
                    src: i.src,
                    alt: i.alt || '',
                    width: i.naturalWidth || i.width || 0,
                    height: i.naturalHeight || i.height || 0
                }));
                
                const genImgs = imgs.filter(i => 
                    (i.width >= 150 && i.height >= 150) || 
                    i.src.includes('oaiusercontent') || 
                    i.src.includes('blob:')
                );

                return {
                    hasStop: hasStop,
                    genImgsCount: genImgs.length
                };
            }""")

            if status["hasStop"]:
                saw_stop_button = True
            elif saw_stop_button:
                # Stop button was visible and has now disappeared
                time.sleep(2.5)  # buffer for image rendering / decoding
                break
            elif elapsed > 8 and not status["hasStop"]:
                # If short text completed quickly without catching stop button
                break

        # Extract text and images
        return self._extract_results()

    def _extract_results(self) -> Dict[str, Any]:
        """Extract text and generated images from the page."""
        try:
            # 1. Text extraction
            body_text = self._page.evaluate("() => document.body.innerText")
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]

            response_text = ""
            if "ChatGPT said:" in lines:
                start_idx = lines.index("ChatGPT said:") + 1
                collected = []
                for l in lines[start_idx:]:
                    if any(stop_word in l for stop_word in ["ChatGPT can make mistakes", "Ask ChatGPT", "Latest response", "Response complete"]):
                        break
                    collected.append(l)
                response_text = "\n".join(collected).strip()
            else:
                response_text = "\n".join(lines[-6:]).strip()

            # 2. Image extraction
            images_data = self._page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const candidates = imgs.filter(i => {
                    const w = i.naturalWidth || i.width || 0;
                    const h = i.naturalHeight || i.height || 0;
                    const src = i.src || '';
                    const alt = (i.alt || '').toLowerCase();
                    const isAvatar = (w < 100 && h < 100) || alt.includes('avatar') || alt.includes('profile');
                    return !isAvatar && (w >= 150 || src.includes('oaiusercontent') || src.includes('blob:'));
                });
                return candidates.map((img, idx) => ({
                    index: idx + 1,
                    src: img.src,
                    alt: img.alt || '',
                    width: img.naturalWidth || img.width,
                    height: img.naturalHeight || img.height
                }));
            }""")

            saved_images = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for item in images_data:
                src = item["src"]
                idx = item["index"]

                # Download via in-browser fetch (handles auth cookies and blob URLs)
                b64_data = self._page.evaluate("""async (url) => {
                    try {
                        const res = await fetch(url, { credentials: 'include' });
                        const blob = await res.blob();
                        return new Promise((resolve) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    } catch (e) {
                        return null;
                    }
                }""", src)

                data_bytes = None
                ext = "png"
                if b64_data and "," in b64_data:
                    header, b64_str = b64_data.split(",", 1)
                    if "image/jpeg" in header:
                        ext = "jpg"
                    elif "image/webp" in header:
                        ext = "webp"
                    data_bytes = base64.b64decode(b64_str)
                else:
                    try:
                        img_el = self._page.locator(f'img[src="{src}"]').first
                        data_bytes = img_el.screenshot()
                    except Exception:
                        pass

                if data_bytes:
                    filename = f"chatgpt_{timestamp}_{idx}.{ext}"
                    save_path = self.images_dir / filename
                    with open(save_path, "wb") as f:
                        f.write(data_bytes)
                    logger.info(f"✓ Saved image: {save_path}")

                    saved_images.append({
                        "index": idx,
                        "saved_path": str(save_path.resolve()),
                        "url": src,
                        "alt": item["alt"],
                        "width": item["width"],
                        "height": item["height"]
                    })

            return {
                "success": True,
                "text": response_text,
                "images": saved_images,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error extracting results: {e}")
            return {"success": False, "error": str(e)}

    def stop(self):
        """Close connection to browser without closing Brave itself."""
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        logger.info("Disconnected from Brave.")
