"""
Playwright automation for X (Twitter) DM.
Opens a browser, navigates to X, and types the DM message.
Demo mode: writes the message but does NOT click Send.
"""

import asyncio
import time
from pathlib import Path

from playwright.async_api import async_playwright


# Directory for screenshots
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
AUTH_FILE = Path(__file__).resolve().parent.parent.parent / "auth.json"


async def _type_dm(
    message: str,
    recipient_handle: str = "",
    auth_file: Path = AUTH_FILE,
    headless: bool = False,
    typing_delay: int = 50,
):
    """
    Open X.com in a browser and type a DM message.
    Does NOT click the Send button (demo mode).

    Args:
        message: The DM text to type
        recipient_handle: The @handle to send DM to (optional)
        auth_file: Path to Playwright saved auth state
        headless: Run browser in headless mode (False for demo)
        typing_delay: Milliseconds between keystrokes (for demo effect)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    storage_state = str(auth_file) if auth_file.exists() else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        context_kwargs = {}
        if storage_state:
            context_kwargs["storage_state"] = storage_state

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            **context_kwargs,
        )
        page = await context.new_page()

        # Navigate to X messages
        if recipient_handle:
            handle = recipient_handle.lstrip("@")
            await page.goto(
                f"https://x.com/messages/compose?recipient={handle}",
                wait_until="networkidle",
            )
        else:
            await page.goto(
                "https://x.com/messages",
                wait_until="networkidle",
            )

        # Wait for DM input area to appear
        await page.wait_for_timeout(3000)

        # Try to find the DM text input
        dm_input = page.get_by_test_id("dmComposerTextInput")

        # Fallback: try common DM input selectors
        if not await dm_input.count():
            dm_input = page.locator(
                '[data-testid="dmComposerTextInput"], '
                '[role="textbox"][data-testid*="dm"], '
                'div[contenteditable="true"]'
            ).first

        if await dm_input.count():
            # Click to focus
            await dm_input.click()
            await page.wait_for_timeout(500)

            # Type the message character by character (demo effect)
            for char in message:
                await dm_input.press_sequentially(
                    char, delay=typing_delay
                )

            # Take screenshot of the typed message
            screenshot_path = OUTPUT_DIR / "dm_typed.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"\n  📸 Screenshot saved: {screenshot_path}")
            print("  ⚠️  Message typed but NOT sent (demo mode)")
        else:
            # Take screenshot even if input not found
            screenshot_path = OUTPUT_DIR / "dm_page.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"\n  📸 Page screenshot saved: {screenshot_path}")
            print(
                "  ⚠️  Could not find DM input field. "
                "Make sure you're logged in to X."
            )

        # Keep browser open for 10 seconds so user can see the demo
        print("  ⏳ Browser will close in 10 seconds...")
        await page.wait_for_timeout(10000)

        await browser.close()


def send_dm_via_playwright(
    message: str,
    recipient_handle: str = "",
    headless: bool = False,
):
    """
    Synchronous wrapper for the Playwright DM automation.

    Args:
        message: The DM text to type
        recipient_handle: The @handle to send DM to
        headless: Run in headless mode
    """
    asyncio.run(
        _type_dm(
            message=message,
            recipient_handle=recipient_handle,
            headless=headless,
        )
    )


if __name__ == "__main__":
    # Quick test
    send_dm_via_playwright(
        message="Hey! Bu bir IntroAgent test mesajıdır 🤖",
        recipient_handle="",
        headless=False,
    )
