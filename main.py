# uptime_bot.py
from pyrogram import Client, filters
import asyncio
import aiohttp
import os

# ------------------ CONFIG ------------------
API_ID = 22959128 #int(os.getenv("API_ID"))  # Telegram API ID
API_HASH = "d9947be127cccae84fc586920d507183"# os.getenv("API_HASH")   # Telegram API Hash
BOT_TOKEN = "7106861798:AAHnPeO4R9_TRGT2vxT3euw3Xto2edz64pI" # os.getenv("BOT_TOKEN") # Telegram Bot Token
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Aapka Telegram ID jahan alerts bhejna hai

# List of bot URLs to monitor
BOT_URLS = [
    "https://yourbot1.onrender.com",
    "https://yourbot2.onrender.com"
]

PING_INTERVAL = 120  # in seconds (2 min)
# -------------------------------------------

app = Client("uptime_monitor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
            await asyncio.gather(*tasks)
            await asyncio.sleep(PING_INTERVAL)

@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply("🤖 Uptime Monitor Bot is running!")

async def main():
    async with app:
        await monitor_bots()  # start monitoring

if __name__ == "__main__":
    asyncio.run(main())
