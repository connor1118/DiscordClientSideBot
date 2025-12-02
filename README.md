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
2. Create a `.env` file with your credentials:
   ```env
   DISCORD_EMAIL=you@example.com
   DISCORD_PASSWORD=your-password
   DISCORD_CHANNEL_URL=https://discord.com/channels/<guild>/<channel>
   ```
3. Prepare your schedule. When you run the script, you will be prompted for each message and its delay:
   - Enter the message text.
   - Enter the number of seconds to wait before sending that message.
   - Repeat until you leave the message text blank to finish.
   - If you skip all messages, a sample schedule is used.

## Running
```bash
python main.py
```
The script opens Chromium (not headless), logs in if necessary, and posts each message after its own delay.

## Notes
- Keep the browser window open until all messages are sent.
- Do not use this script to violate Discord's Terms of Service.
