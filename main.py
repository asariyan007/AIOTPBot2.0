import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import httpx
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
API_URLS = os.getenv("API_URLS").split(",")

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Runtime Data
bot_status = {"on": False}
groups = set()
credits = {}

# Util: Check owner
def is_owner(user_id):
    return user_id == OWNER_ID

# Command Handlers
@dp.message_handler(commands=['on'])
async def cmd_on(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("🚫 You are not authorized.")
    bot_status["on"] = True
    await message.reply("✅ Bot is now ON.")

@dp.message_handler(commands=['off'])
async def cmd_off(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("✅ Bot is now OFF.")
    bot_status["on"] = False

@dp.message_handler(commands=['status'])
async def cmd_status(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("🚫 You are not authorized.")
    state = "ON ✅" if bot_status["on"] else "OFF ❌"
    await message.reply(f"ℹ️ Bot Status: {state}")

@dp.message_handler(commands=['addgroup'])
async def cmd_addgroup(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("🚫 You are not authorized.")
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /addgroup <group_chat_id>")
    groups.add(args[1])
    await message.reply(f"✅ Added group {args[1]}.")

@dp.message_handler(commands=['rmvgroup'])
async def cmd_rmvgroup(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("🚫 You are not authorized.")
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /rmvgroup <group_chat_id>")
    groups.discard(args[1])
    await message.reply(f"✅ Removed group {args[1]}.")

@dp.message_handler(commands=['cngcredit'])
async def cmd_cngcredit(message: types.Message):
    if not is_owner(message.from_user.id):
        return await message.reply("🚫 You are not authorized.")
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        return await message.reply("Usage: /cngcredit <group_chat_id> <new_credit>")
    credits[args[1]] = args[2]
    await message.reply(f"✅ Updated credit for group {args[1]}.")

# Periodic OTP fetcher
async def fetch_loop():
    while True:
        if bot_status["on"]:
            for api in API_URLS:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        r = await client.get(api)
                        if r.status_code == 200 and r.json():
                            data = r.json()
                            for otp in data:
                                text = format_otp_message(otp)
                                for group in groups:
                                    credit = credits.get(group, "TEAM ELITE X")
                                    final_text = text + f"\n\n<em>Powered By {credit}</em>"
                                    await bot.send_message(int(group), final_text)
                except Exception as e:
                    print(f"[ERROR] {e}")
        await asyncio.sleep(10)

def format_otp_message(data):
    return (
        f"✨ <b>NEW CODE RECEIVED</b> ✨\n\n"
        f"🕒 <b>Time:</b> {data.get('time','')}\n"
        f"📅 <b>Date:</b> {data.get('date','')}\n"
        f"🌍 <b>Country:</b> {data.get('country','')} {data.get('flag','')}\n"
        f"⚙️ <b>Service:</b> {data.get('service','')}\n"
        f"☎️ <b>Number:</b> {data.get('number','')}\n"
        f"🔑 <b>OTP:</b> {data.get('otp','')}\n"
        f"✉️ <b>Full Message:</b>\n<code>{data.get('message','')}</code>\n\n"
        f"📄 <i>Note: ~ Wait at least 30 seconds to get your requested OTP code ~</i>"
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(fetch_loop())
    executor.start_polling(dp)