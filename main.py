import asyncio
import hashlib
import logging
import sqlite3
import httpx
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage

# ----------------- CONFIG -----------------
BOT_TOKEN = "8496694021:AAGyZFZoHM9PqCgYo70df4gVAZku8C_bF78"
OWNER_ID = 5359578794
API_URL = "https://techflare.2cloud.top/fbagentapi.php"
WEBHOOK_PATH = f"/bot/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_STATIC_URL')}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ----------------- DATABASE -----------------
conn = sqlite3.connect("bot_data.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY, credit TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS bot_status (id INTEGER PRIMARY KEY, status TEXT)")
cur.execute("INSERT OR IGNORE INTO bot_status (id, status) VALUES (1, 'off')")
conn.commit()

def set_status(status: str):
    cur.execute("UPDATE bot_status SET status = ? WHERE id = 1", (status,))
    conn.commit()

def get_status() -> str:
    cur.execute("SELECT status FROM bot_status WHERE id = 1")
    return cur.fetchone()[0]

def add_group(group_id: int):
    cur.execute("INSERT OR IGNORE INTO groups (group_id, credit) VALUES (?, 'TEAM ELITE X')", (group_id,))
    conn.commit()

def rmv_group(group_id: int):
    cur.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
    conn.commit()

def update_credit(group_id: int, new_credit: str):
    cur.execute("UPDATE groups SET credit = ? WHERE group_id = ?", (new_credit, group_id))
    conn.commit()

def get_groups():
    cur.execute("SELECT group_id FROM groups")
    return [row[0] for row in cur.fetchall()]

def get_credit(group_id: int) -> str:
    cur.execute("SELECT credit FROM groups WHERE group_id = ?", (group_id,))
    r = cur.fetchone()
    return r[0] if r else "TEAM ELITE X"

# ----------------- OTP CACHE -----------------
sent_hashes = set()
def is_unique(otp: str) -> bool:
    h = hashlib.sha256(otp.encode()).hexdigest()
    if h in sent_hashes:
        return False
    sent_hashes.add(h)
    return True

# ----------------- BUTTONS -----------------
def otp_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Main Channel", url="https://t.me/TEAM_ELITE_X")],
        [InlineKeyboardButton(text="Numbers File", url="https://t.me/TEAM_ELITE_X")]
    ])

# ----------------- OTP FETCH & SEND -----------------
async def fetch_and_send():
    while True:
        if get_status() == "on":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(API_URL, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        for entry in data:
                            otp = str(entry.get("otp", "")).strip()
                            number = entry.get("number", "")
                            if otp and is_unique(otp):
                                msg = (
                                    f"🔥 <b>New OTP Received</b> 🔥\n\n"
                                    f"📞 <b>Number:</b> <code>{number}</code>\n"
                                    f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                                )
                                for gid in get_groups():
                                    credit = get_credit(gid)
                                    final = msg + f"🟢 <i>Powered By {credit}</i>"
                                    try:
                                        await bot.send_message(chat_id=gid, text=final, reply_markup=otp_buttons())
                                    except Exception as e:
                                        logging.warning(f"Couldn't send to group {gid}: {e}")
            except Exception as e:
                logging.warning(f"Error fetching OTP: {e}")
        await asyncio.sleep(5)

# ----------------- COMMANDS -----------------
@dp.message()
async def handle_commands(msg: types.Message):
    if not msg.text.startswith("/"):
        return

    user_id = msg.from_user.id
    command_parts = msg.text.strip().split(maxsplit=2)
    command = command_parts[0].lower()

    if user_id != OWNER_ID:
        await msg.reply("⚠️ You are not allowed to use this command.")
        return

    if command == "/on":
        set_status("on")
        await msg.reply("✅ Bot is now ON.")
    elif command == "/off":
        set_status("off")
        await msg.reply("⛔ Bot is now OFF.")
    elif command == "/status":
        status = get_status()
        await msg.reply(f"ℹ️ Bot status: {status.upper()}")
    elif command == "/addgroup":
        if len(command_parts) < 2:
            return await msg.reply("❌ Usage: /addgroup <group_id>")
        try:
            gid = int(command_parts[1])
            add_group(gid)
            await msg.reply(f"✅ Added group {gid}.")
        except:
            await msg.reply("❌ Invalid group ID.")
    elif command == "/rmvgroup":
        if len(command_parts) < 2:
            return await msg.reply("❌ Usage: /rmvgroup <group_id>")
        try:
            gid = int(command_parts[1])
            rmv_group(gid)
            await msg.reply(f"✅ Removed group {gid}.")
        except:
            await msg.reply("❌ Invalid group ID.")
    elif command == "/cngcredit":
        if len(command_parts) < 3:
            return await msg.reply("❌ Usage: /cngcredit <group_id> <new_credit>")
        try:
            gid = int(command_parts[1])
            credit = command_parts[2]
            update_credit(gid, credit)
            await msg.reply(f"✅ Credit updated for {gid}.")
        except:
            await msg.reply("❌ Invalid input.")
    else:
        await msg.reply("⚠️ Unknown command.")

# ----------------- WEBHOOK SETUP -----------------
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(fetch_and_send())

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
