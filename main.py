import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from dotenv import load_dotenv
from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


@dataclass
class ScheduledMessage:
    content: str
    delay_seconds: float


async def wait_for_textbox(page: Page) -> None:
    await page.wait_for_selector('div[role="textbox"]', timeout=60_000)


async def click_open_in_browser(page: Page) -> None:
    """Click the "Open Discord in your browser" button if it appears."""
    try:
        await page.get_by_role("button", name="Open Discord in your browser").click(
            timeout=5_000
        )
    except PlaywrightTimeoutError:
        return


async def ensure_logged_in(page: Page, email: str, password: str, channel_url: str) -> None:
    """Log into Discord if the session is not already authenticated."""
    # Start from the login page to avoid Discord app interstitials.
    await page.goto("https://discord.com/login", wait_until="domcontentloaded")
    await click_open_in_browser(page)

    # If we're already authenticated, we should see a textbox after the channel loads.
    try:
        await wait_for_textbox(page)
    except PlaywrightTimeoutError:
        email_locator = page.locator('input[name="email"]')
        password_locator = page.locator('input[name="password"]')

        await email_locator.wait_for(timeout=60_000)
        await email_locator.fill(email)
        await password_locator.fill(password)

        await page.locator('button[type="submit"]').click()

    # Navigate directly to the channel after ensuring we're signed in.
    await page.goto(channel_url, wait_until="domcontentloaded")
    await click_open_in_browser(page)
    await wait_for_textbox(page)


def prompt_float(prompt: str, *, allow_empty: bool = False) -> Optional[float]:
    while True:
        raw = input(prompt).strip()
        if allow_empty and not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number (seconds).")


def load_saved_messages(schedule_path: Path) -> List[ScheduledMessage]:
    if not schedule_path.exists():
        return []

    try:
        data = json.loads(schedule_path.read_text())
        messages = [ScheduledMessage(**item) for item in data]
        return messages
    except (json.JSONDecodeError, TypeError, KeyError):
        print("Saved schedule was invalid. Starting fresh.")
        return []


def save_messages(schedule_path: Path, messages: List[ScheduledMessage]) -> None:
    payload = [msg.__dict__ for msg in messages]
    schedule_path.write_text(json.dumps(payload, indent=2))


def describe_schedule(messages: List[ScheduledMessage]) -> None:
    if not messages:
        print("(no scheduled messages yet)\n")
        return

    print("Current schedule:")
    for idx, msg in enumerate(messages, start=1):
        print(f"  {idx}. send after {msg.delay_seconds} seconds: {msg.content}")
    print()


def prompt_index(max_index: int, action: str) -> Optional[int]:
    if max_index == 0:
        print("No messages to modify.\n")
        return None

    while True:
        raw = input(f"Choose which message to {action} (1-{max_index}): ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= value <= max_index:
            return value - 1

        print(f"Please choose a number between 1 and {max_index}.")


def manage_schedule(schedule_path: Path) -> List[ScheduledMessage]:
    """Console UI to view, add, edit, and persist the schedule."""

    messages = load_saved_messages(schedule_path)

    if not messages:
        print("No saved schedule found. You'll start with an empty list.\n")

    while True:
        describe_schedule(messages)
        print("Menu:")
        print("  1) Add a message")
        print("  2) Edit a message")
        print("  3) Delete a message")
        print("  4) Clear all messages")
        print("  5) Start sending (save first)")
        print("  6) Load sample schedule")
        print("  q) Quit without sending")

        choice = input("Select an option: ").strip().lower()

        if choice == "1":
            content = input("Message content: ").strip()
            if not content:
                print("Content cannot be empty.\n")
                continue

            delay = prompt_float("Delay (seconds) before sending this message: ")
            messages.append(ScheduledMessage(content=content, delay_seconds=delay))
            save_messages(schedule_path, messages)
            print("Saved.\n")
        elif choice == "2":
            index = prompt_index(len(messages), "edit")
            if index is None:
                continue

            current = messages[index]
            new_content = input(
                f"New content (leave blank to keep '{current.content}'): "
            ).strip()
            new_delay = prompt_float(
                f"New delay in seconds (current {current.delay_seconds}, blank to keep): ",
                allow_empty=True,
            )

            if new_content:
                current.content = new_content
            if new_delay is not None:
                current.delay_seconds = new_delay

            save_messages(schedule_path, messages)
            print("Updated.\n")
        elif choice == "3":
            index = prompt_index(len(messages), "delete")
            if index is None:
                continue

            removed = messages.pop(index)
            save_messages(schedule_path, messages)
            print(f"Removed: {removed.content}\n")
        elif choice == "4":
            messages.clear()
            save_messages(schedule_path, messages)
            print("Cleared schedule.\n")
        elif choice == "5":
            if not messages:
                print("Add at least one message before starting.\n")
                continue

            save_messages(schedule_path, messages)
            print("Saved schedule. Starting...\n")
            return messages
        elif choice == "6":
            messages = [
                ScheduledMessage("Hello from the Discord browser automation demo!", 5),
                ScheduledMessage("Each message can have its own delay.", 10),
                ScheduledMessage("Update the list in main.py to fit your needs.", 15),
            ]
            save_messages(schedule_path, messages)
            print("Loaded sample schedule.\n")
        elif choice == "q":
            raise SystemExit("Exiting without sending messages.")
        else:
            print("Please select a valid option.\n")


async def send_messages(page: Page, messages: Iterable[ScheduledMessage]) -> None:
    print("Sending messages. Press Ctrl+C to stop.\n")

    async def run_message_loop(message: ScheduledMessage) -> None:
        while True:
            await asyncio.sleep(message.delay_seconds)
            textbox = page.locator('div[role="textbox"]')
            await textbox.fill("")
            await textbox.type(message.content)
            await textbox.press("Enter")
            print(f"Sent: {message.content}")

    tasks = [asyncio.create_task(run_message_loop(msg)) for msg in messages]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        for task in tasks:
            task.cancel()


async def main() -> None:
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    schedule_path = script_dir / "scheduled_messages.json"

    email = os.environ.get("DISCORD_EMAIL")
    password = os.environ.get("DISCORD_PASSWORD")
    channel_url = os.environ.get("DISCORD_CHANNEL_URL")

    if not all([email, password, channel_url]):
        raise SystemExit(
            "DISCORD_EMAIL, DISCORD_PASSWORD, and DISCORD_CHANNEL_URL must be set. "
            f"Looked for a .env file at: {env_path}"
        )

    messages = manage_schedule(schedule_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            await ensure_logged_in(page, email, password, channel_url)
            await send_messages(page, messages)
        except KeyboardInterrupt:
            print("\nStopping message loop...")
        finally:
            await asyncio.sleep(1)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
