"""
Example of importing and using ChatGPTAutomator in your own Python projects.
"""
from chatgpt_automator import ChatGPTAutomator

def main():
    # 1. Initialize automator
    # If Brave is running on port 9222, it connects directly.
    # Otherwise, it launches Brave.
    automator = ChatGPTAutomator(port=9222, profile_mode="auto", timeout=180)

    if not automator.start():
        print("Failed to start or connect to Brave.")
        return

    try:
        # Example 1: Text prompt
        print("Sending text prompt...")
        text_res = automator.send_prompt("Explain quantum computing in 2 simple sentences.", new_chat=True)
        print("Text response:")
        print(text_res["text"])

        # Example 2: Image generation prompt
        print("\nSending image generation prompt...")
        img_res = automator.send_prompt("Create an image of a red vintage sports car on a winding mountain road.")
        print("Assistant message:")
        print(img_res["text"])

        print("\nGenerated images:")
        for img in img_res.get("images", []):
            print(f"- Saved at: {img['saved_path']}")
            print(f"- Source URL: {img['url']}")

    finally:
        automator.stop()

if __name__ == "__main__":
    main()
