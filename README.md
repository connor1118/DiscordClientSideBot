# Discord Browser Message Scheduler

This script uses Playwright to automate the browser version of Discord and send predefined messages at unique intervals for each message.

## Prerequisites
- Python 3.10+
- Installed browser binaries for Playwright (`python -m playwright install chromium`)
- Discord account credentials
- A channel URL the account can post to (e.g., `https://discord.com/channels/<guild_id>/<channel_id>`)

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
2. Create a `.env` file in the same directory as `main.py` with your credentials:
   ```env
   DISCORD_EMAIL=you@example.com
   DISCORD_PASSWORD=your-password
   DISCORD_CHANNEL_URL=https://discord.com/channels/<guild>/<channel>
   ```
3. Prepare your schedule (optional). The script saves your messages and delays to `scheduled_messages.json` next to `main.py` so you only set them once.

## Running
```bash
python main.py
```

You'll see a simple menu to manage the saved schedule:
- Add, edit, or delete messages and their per-message delays.
- Load a sample schedule, or clear everything.
- Start sending using the saved schedule (it auto-saves after each change).

When sending starts, the script:
- Opens Chromium (not headless).
- Clicks **Open Discord in your browser** if that prompt appears.
- Logs in with your `.env` credentials if not already authenticated.
- Repeatedly sends each message after its own delay until you press **Ctrl+C**.

## Notes
- Keep the browser window open until you stop the loop (Ctrl+C).
- Do not use this script to violate Discord's Terms of Service.
