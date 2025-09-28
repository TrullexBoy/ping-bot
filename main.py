# uptime_bot.py
from pyrogram import Client, filters
import asyncio
import aiohttp
import os

# ------------------ CONFIG ------------------
API_ID = 22959128  # Telegram API ID
API_HASH = "d9947be127cccae84fc586920d507183"  # Telegram API Hash
BOT_TOKEN = "7106861798:AAHnPeO4R9_TRGT2vxT3euw3Xto2edz64pI"  # Telegram Bot Token
ADMIN_ID = -1001942149963  # Telegram Channel/Chat ID jahan alerts bhejne hain

# List of bot URLs to monitor
BOT_URLS = [
    "https://webxzonebot.onrender.com",
    "https://the-cloner-boy.onrender.com"
]

PING_INTERVAL = 120  # seconds (2 minutes)
# -------------------------------------------

app = Client("uptime_monitor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------ PING FUNCTION ------------------
async def ping_bot(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                print(f"{url} is UP ✅")
            else:
                print(f"{url} is DOWN ❌ Status: {resp.status}")
                await app.send_message(ADMIN_ID, f"⚠️ {url} is DOWN! Status: {resp.status}")
    except Exception as e:
        print(f"{url} is DOWN ❌ Error: {e}")
        await app.send_message(ADMIN_ID, f"⚠️ {url} is DOWN! Error: {e}")

# ------------------ MONITOR LOOP ------------------
async def monitor_bots():
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [ping_bot(session, url) for url in BOT_URLS]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(PING_INTERVAL)

# ------------------ COMMANDS ------------------
@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply("🤖 Uptime Monitor Bot is running!")

@app.on_message(filters.command("status") & filters.private)
async def status(_, message):
    reply_text = "🤖 Bot Status:\n\n"
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in BOT_URLS:
            tasks.append(check_status(session, url))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        reply_text += "\n".join(results)
    await message.reply(reply_text)

async def check_status(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return f"✅ {url} is UP"
            else:
                return f"⚠️ {url} is DOWN (Status: {resp.status})"
    except Exception as e:
        return f"❌ {url} is DOWN (Error: {e})"

# ------------------ MAIN ------------------
async def main():
    async with app:
        # Start monitor_bots in background
        app.loop.create_task(monitor_bots())
        print("🤖 Uptime Monitor Bot is running...")
        await app.idle()  # Keep bot alive and commands responsive

# ------------------ RUN ------------------
if __name__ == "__main__":
    asyncio.run(main())
