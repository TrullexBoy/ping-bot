# main.py
import os
import asyncio
import threading
from flask import Flask
import aiohttp
from pyrogram import Client, filters, idle

# ------------------ CONFIG (use env in production) ------------------
API_ID = int(os.environ.get("API_ID", "22959128"))
API_HASH = os.environ.get("API_HASH", "d9947be127cccae84fc586920d507183")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6282720780:AAEnFf_NduuGXCaCKfa7-GpdFHaAvHugUCc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "-1001942149963"))

# List of bot URLs to monitor
BOT_URLS = [
    os.environ.get("URL1", "https://webxzonebot.onrender.com"),
    os.environ.get("URL2", "https://the-cloner-boy.onrender.com"),
]

PING_INTERVAL = int(os.environ.get("PING_INTERVAL", "120"))  # seconds
PORT = int(os.environ.get("PORT", "10000"))  # Render will set this

# --------------------------------------------------------------------

# Pyrogram client
app = Client("uptime_monitor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask web server for Render health-check + simple status page
web = Flask(__name__)

# Shared aiohttp session (created at startup)
SESSION: aiohttp.ClientSession | None = None


# ------------------ PING / STATUS LOGIC ------------------
async def ping_bot(url: str):
    global SESSION
    assert SESSION is not None, "HTTP session not started"
    try:
        async with SESSION.get(url, timeout=10) as resp:
            if resp.status == 200:
                print(f"[PING] {url} is UP ✅")
                return True
            else:
                print(f"[PING] {url} is DOWN ❌ Status: {resp.status}")
                # notify admin
                try:
                    await app.send_message(ADMIN_ID, f"⚠️ {url} is DOWN! Status: {resp.status}")
                except Exception as err:
                    print("Failed to send admin message:", err)
                return False
    except Exception as e:
        print(f"[PING] {url} is DOWN ❌ Error: {e}")
        try:
            await app.send_message(ADMIN_ID, f"⚠️ {url} is DOWN! Error: {e}")
        except Exception as err:
            print("Failed to send admin message:", err)
        return False


async def monitor_bots():
    print("[monitor] background monitor started")
    while True:
        tasks = [ping_bot(url) for url in BOT_URLS]
        # run parallel, swallow exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # optional: print small summary
        ups = sum(1 for r in results if r is True)
        print(f"[monitor] checked {len(BOT_URLS)} URLs — {ups} UP")
        await asyncio.sleep(PING_INTERVAL)


async def check_status_text():
    global SESSION
    assert SESSION is not None
    tasks = []
    for url in BOT_URLS:
        async def _check(u=url):
            try:
                async with SESSION.get(u, timeout=10) as resp:
                    if resp.status == 200:
                        return f"✅ {u} is UP"
                    else:
                        return f"⚠️ {u} is DOWN (Status: {resp.status})"
            except Exception as e:
                return f"❌ {u} is DOWN (Error: {e})"
        tasks.append(_check())
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # convert any exceptions to string
    return [str(r) for r in results]


# ------------------ TELEGRAM HANDLERS ------------------
@app.on_message(filters.command("start"))
async def start_handler(_, message):
    print(f"[handler] /start from {message.chat.id}")
    await message.reply_text("🤖 Uptime Monitor Bot is running! Use /status to see monitored URLs.")


@app.on_message(filters.command("status"))
async def status_handler(_, message):
    print(f"[handler] /status from {message.chat.id}")
    results = await check_status_text()
    await message.reply("\n".join(results))


# ------------------ FLASK WEB ------------------
@web.route("/")
def homepage():
    # Use a new event loop to call async check (Flask thread is sync)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(check_status_text())
    finally:
        loop.close()
    # minimal HTML
    html = "<html><head><meta http-equiv='refresh' content='10'></head><body>"
    html += "<h3>Uptime Monitor</h3><pre>"
    html += "\n".join(results)
    html += "</pre></body></html>"
    return html


def start_flask():
    # run Flask in separate daemon thread so it won't block shutdown
    web.run(host="0.0.0.0", port=PORT)


# ------------------ LIFECYCLE (startup/shutdown) ------------------
async def main():
    global SESSION
    # create shared HTTP session
    SESSION = aiohttp.ClientSession()
    # start pyrogram
    await app.start()
    me = await app.get_me()
    print(f"[pyrogram] Logged in as @{me.username} (id={me.id})")
    # start monitor in background
    asyncio.create_task(monitor_bots())
    # start flask in a daemon thread (so Render health checks work)
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print(f"[web] Flask started on port {PORT} (thread={flask_thread.name})")
    # keep running until process terminated
    await idle()
    # shutdown
    await SESSION.close()
    await app.stop()
    print("[shutdown] clean exit")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("exiting...")
