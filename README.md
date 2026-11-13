# agent_custom_tools

A curated collection of autonomous agent tools, browser automations, and custom integrations.

---

## 📦 Tools Included

### 1. `chatgpt_chat`
Automate interactions with [chatgpt.com](https://chatgpt.com) using your installed **Brave Browser** via Chrome DevTools Protocol (CDP).
- **Supports Logged-In Sessions**: Reuses your existing Brave profile to bypass bot checks and use authenticated features without entering credentials.
- **Text & Image Outputs**: Extracts formatted text responses and downloads full-resolution DALL-E / GPT-4o generated images locally.
- **Dual Profile Modes**: Run on your main Brave profile or alongside your normal browsing via a dedicated automation profile.
- **Interactive REPL & CLI**: Includes interactive terminal chat mode and single-prompt CLI execution.

See [`chatgpt_chat/README.md`](./chatgpt_chat/README.md) for full documentation and usage details.

---

## 🚀 Quick Start (`chatgpt_chat`)

```bash
cd chatgpt_chat
pip install -r requirements.txt

# Run a prompt with image generation
python run.py --prompt "create a photo of an astronaut on Mars"

# Or enter interactive chat mode
python run.py
```
