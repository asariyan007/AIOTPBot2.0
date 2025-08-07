import asyncio
import hashlib
import logging
import sqlite3
import httpx
import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ----------- CONFIG -------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_URL = os.getenv("API_URLS")

# ----------- BOT & DISPATCHER -------------
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ----------- DATABASE -------------
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
    cur.execute("INSERT OR IGNORE INTO groups (group_id, credit) VALUES (?, '𝙎𝙖𝙡𝙚𝙨 𝙎𝙩𝙤𝙧𝙢 🌍')", (group_id,))
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
    return r[0] if r else "𝙎𝙖𝙡𝙚𝙨 𝙎𝙩𝙤𝙧𝙢 🌍"

# ----------- OTP CACHE -------------
sent_hashes = set()
def is_unique(otp: str) -> bool:
    h = hashlib.sha256(otp.encode()).hexdigest()
    if h in sent_hashes:
        return False
    sent_hashes.add(h)
    return True

# ----------- BUTTONS -------------
def otp_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Main Channel", url="https://t.me/+cbH_C9D9Rog4NWE1")],
        [InlineKeyboardButton(text="Numbers File", url="https://t.me/+cbH_C9D9Rog4NWE1")]
    ])

# ----------- OTP FETCH & SEND LOOP -------------
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
                                    final = msg + f"\n🟢 <i>Powered By {credit}</i>"
                                    await bot.send_message(chat_id=gid, text=final, reply_markup=otp_buttons())
            except Exception as e:
                logging.warning(f"Error fetching OTP: {e}")
        await asyncio.sleep(5)

# ----------- COMMAND HANDLERS -------------
@dp.message(F.text.startswith("/on"))
async def cmd_on(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    set_status("on")
    await msg.answer("✅ Bot is now ON.")

@dp.message(F.text.startswith("/off"))
async def cmd_off(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    set_status("off")
    await msg.answer("⛔ Bot is now OFF.")

@dp.message(F.text.startswith("/status"))
async def cmd_status(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    await msg.answer(f"ℹ️ Bot status: {get_status().upper()}")

@dp.message(F.text.startswith("/addgroup"))
async def cmd_addgroup(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    try:
        gid = int(msg.text.split()[1])
        add_group(gid)
        await msg.answer(f"✅ Added group {gid}.")
    except:
        await msg.answer("❌ Usage: /addgroup <group_id>")

@dp.message(F.text.startswith("/rmvgroup"))
async def cmd_rmvgroup(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    try:
        gid = int(msg.text.split()[1])
        rmv_group(gid)
        await msg.answer(f"✅ Removed group {gid}.")
    except:
        await msg.answer("❌ Usage: /rmvgroup <group_id>")

@dp.message(F.text.startswith("/cngcredit"))
async def cmd_cngcredit(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return await msg.answer("⚠️ You are not allowed to use this command.")
    try:
        parts = msg.text.split(maxsplit=2)
        gid = int(parts[1])
        new_cr = parts[2]
        update_credit(gid, new_cr)
        await msg.answer(f"✅ Credit updated for {gid}.")
    except:
        await msg.answer("❌ Usage: /cngcredit <group_id> <new_credit>")

# ----------- MAIN STARTUP -------------
async def main():
    # Start OTP loop
    asyncio.create_task(fetch_and_send())

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
