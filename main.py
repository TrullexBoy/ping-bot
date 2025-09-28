# uptime_bot.py
from pyrogram import Client, filters
import asyncio
import aiohttp
import os

# ------------------ CONFIG ------------------
API_ID = 22959128
API_HASH = "d9947be127cccae84fc586920d507183"
BOT_TOKEN = "6282720780:AAEnFf_NduuGXCaCKfa7-GpdFHaAvHugUCc"
ADMIN_ID = -1001942149963

BOT_URLS = [
    "https://webxzonebot.onrender.com",
    "https://the-cloner-boy.onrender.com"
]

PING_INTERVAL = 120
# -------------------------------------------

app = Client("uptime_monitor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------ PING ------------------
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

async def monitor_bots():
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [ping_bot(session, url) for url in BOT_URLS]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(PING_INTERVAL)

# ------------------ STATUS ------------------
async def check_status(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return f"✅ {url} is UP"
            else:
                return f"⚠️ {url} is DOWN (Status: {resp.status})"
    except Exception as e:
        return f"❌ {url} is DOWN (Error: {e})"

@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply("🤖 Uptime Monitor Bot is running!")

@app.on_message(filters.command("status") & filters.private)
async def status(_, message):
    reply_text = "🤖 Bot Status:\n\n"
    async with aiohttp.ClientSession() as session:
        tasks = [check_status(session, url) for url in BOT_URLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        reply_text += "\n".join(results)
    await message.reply(reply_text)

# ------------------ RUN ------------------
if __name__ == "__main__":
    async def runner():
        async with app:
            app.loop.create_task(monitor_bots())
            print("🤖 Uptime Monitor Bot is running...")
            # replacement for app.idle() in v2.x
            await asyncio.Event().wait()  

    asyncio.run(runner())
