# ChatGPT + Brave Browser Automation

An automation engine designed to interact with [chatgpt.com](https://chatgpt.com) using your **installed Brave Browser**.

It reuses your **already logged-in Brave profile** (or runs a dedicated profile side-by-side), types prompts, waits for completion, and extracts **both formatted text and generated images** (saving images to your local drive automatically).

---

## 🚀 Features

- **Uses Your Real Brave Browser**: Connects via Chrome DevTools Protocol (CDP) to your actual Brave browser. No bot flags, no Cloudflare blocks, and keeps you logged in.
- **Full Image Support**: Detects DALL-E / GPT-4o image generation, downloads full-resolution images through the browser's authenticated context (supporting `blob:`, authenticated CDN links, and WebP/PNG), and saves them to `outputs/images/`.
- **Text & Markdown Output**: Retrieves full assistant answers, preserving formatting and code blocks.
- **Two Flexible Profile Modes**:
  - **Main Profile**: Uses your existing Brave profile directly with all your logins, cookies, and extensions.
  - **Dedicated Profile**: Runs a separate Brave window side-by-side without needing to close your everyday browsing tabs.
- **Interactive CLI & Python API**: Use it via terminal command, interactive chat loop (`ChatGPT >> `), or import into any Python project.

---

## 📁 Project Structure

```text
chatgpt_brave_automation/
├── brave_launcher.py       # Auto-locates Brave and manages CDP port 9222
├── chatgpt_automator.py    # Core automation engine (ChatGPTAutomator class)
├── run.py                  # CLI runner and interactive chat interface
├── example_usage.py        # Code snippet for importing into other scripts
├── launch_brave.bat        # 1-click batch launcher for Brave with remote debugging
├── requirements.txt        # Python dependencies
└── outputs/
    └── images/             # Folder where downloaded images are saved
```

---

## 🛠️ Setup & Installation

### 1. Requirements
Ensure Python 3.10+ is installed and install the required library:
```bash
pip install -r requirements.txt
```
*(Only `playwright` is required; no separate browser download is needed because it connects to your existing Brave installation!)*

---

## ⚡ How to Run

### Method 1: Using Your Main Profile (Recommended for Existing Logins)
Chromium browsers (Brave, Chrome) allow remote debugging on your main profile if Brave is started with `--remote-debugging-port=9222`.

1. Double-click `launch_brave.bat` and select **`1`** (Main Profile).
   - If Brave is already open, it will ask to close it first so it can restart with debugging enabled on your main profile.
2. In your terminal, run:
   ```bash
   python run.py --prompt "Generate an image of a neon cybernetic tiger"
   ```
   Or run without `--prompt` for the interactive mode:
   ```bash
   python run.py
   ```

---

### Method 2: Dedicated Profile (Run Alongside Open Brave Windows)
If you have work tabs open and don't want to close your existing Brave windows:

1. Run:
   ```bash
   python run.py --profile dedicated --prompt "Write a short poem about space"
   ```
2. A separate Brave window will open.
3. If not already logged in, log in once in that window. Your login session will be permanently saved in `%LOCALAPPDATA%\BraveSoftware\Brave-ChatGPT-Automation\Profile`. All future runs will remember your login!

---

## 💻 CLI Usage Examples

### 1. Single Text Prompt
```bash
python run.py --prompt "Explain quantum computing in 3 bullets"
```

### 2. Image Generation Prompt
```bash
python run.py --prompt "Create a realistic image of an astronaut drinking coffee on Mars"
```
Generated images will be automatically downloaded and saved to:
`outputs/images/chatgpt_<timestamp>_<index>.png`

### 3. Start a Fresh Conversation (New Chat)
```bash
python run.py --new-chat --prompt "Hello, let's start a new topic."
```

### 4. Interactive Mode
```bash
python run.py
```
You can type multiple prompts, view the outputs, and type `/new` to start a new chat or `exit` to quit.

### 5. Output Raw JSON (For Pipelines / Scripts)
```bash
python run.py --prompt "What is 2+2?" --json
```

---

## 🐍 Using as a Python Library

You can easily integrate `ChatGPTAutomator` into your existing Python applications:

```python
from chatgpt_automator import ChatGPTAutomator

# Initialize
automator = ChatGPTAutomator(port=9222, profile_mode="auto")

if automator.start():
    try:
        # Send prompt
        result = automator.send_prompt("Create an illustration of a cozy rainy library cafe")

        # Access text output
        print("Text:", result["text"])

        # Access generated images
        for img in result.get("images", []):
            print(f"Image saved at: {img['saved_path']}")
            print(f"Image dimensions: {img['width']}x{img['height']}")

    finally:
        automator.stop()
```

---

## 🛡️ Technical Details & Anti-Bot Protection

Standard browser automation (e.g., standard Selenium/Playwright) is routinely blocked by Cloudflare Turnstile and ChatGPT's bot protection.

This tool bypasses those issues natively by:
1. **Connecting via Chrome DevTools Protocol (CDP)** directly to your real Brave executable (`brave.exe`).
2. Setting `navigator.webdriver` to `false` naturally (because it is your genuine browser).
3. Utilizing your existing user profile, cookies, and Cloudflare clearance tokens.
4. Extracting generated images via in-browser authenticated blob fetching and canvas rendering fallbacks.
