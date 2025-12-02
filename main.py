import asyncio
import os
from dataclasses import dataclass
from typing import Iterable, List

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError


@dataclass
class ScheduledMessage:
    content: str
    delay_seconds: float


async def wait_for_textbox(page: Page) -> None:
    await page.wait_for_selector('div[role="textbox"]', timeout=60_000)


async def ensure_logged_in(page: Page, email: str, password: str) -> None:
    """Log into Discord if the session is not already authenticated."""
    await page.goto(os.environ["DISCORD_CHANNEL_URL"], wait_until="networkidle")

    try:
        await wait_for_textbox(page)
        return
    except PlaywrightTimeoutError:
        pass

    email_locator = page.locator('input[name="email"]')
    password_locator = page.locator('input[name="password"]')

    await email_locator.wait_for(timeout=60_000)
    await email_locator.fill(email)
    await password_locator.fill(password)

    await page.locator('button[type="submit"]').click()
    await wait_for_textbox(page)


def prompt_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number (seconds).")


def build_messages() -> List[ScheduledMessage]:
    """Collect messages and unique delays from a simple console UI."""
    print("Configure the messages you want to send. Leave the content blank to finish.\n")
    messages: List[ScheduledMessage] = []

    while True:
        content = input("Message content (leave empty to finish): ").strip()
        if not content:
            break

        delay_seconds = prompt_float("Delay (seconds) before sending this message: ")
        messages.append(ScheduledMessage(content=content, delay_seconds=delay_seconds))
        print("Added.\n")

    if not messages:
        print("No messages provided. Using a sample schedule.\n")
        return [
            ScheduledMessage("Hello from the Discord browser automation demo!", 5),
            ScheduledMessage("Each message can have its own delay.", 10),
            ScheduledMessage("Update the list in main.py to fit your needs.", 15),
        ]

    return messages


async def send_messages(page: Page, messages: Iterable[ScheduledMessage]) -> None:
    for message in messages:
        await asyncio.sleep(message.delay_seconds)
        textbox = page.locator('div[role="textbox"]')
        await textbox.fill("")
        await textbox.type(message.content)
        await textbox.press("Enter")


async def main() -> None:
    load_dotenv()

    email = os.environ.get("DISCORD_EMAIL")
    password = os.environ.get("DISCORD_PASSWORD")
    channel_url = os.environ.get("DISCORD_CHANNEL_URL")

    if not all([email, password, channel_url]):
        raise SystemExit("DISCORD_EMAIL, DISCORD_PASSWORD, and DISCORD_CHANNEL_URL must be set.")

    messages = build_messages()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await ensure_logged_in(page, email, password)
        await send_messages(page, messages)

        await asyncio.sleep(5)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
