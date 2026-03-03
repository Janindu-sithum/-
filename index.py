import asyncio
import time
import os
import json
from datetime import datetime
from telethon import TelegramClient, events, Button, errors
from flask import Flask
from threading import Thread

# --- Flask Server ---
app = Flask('')
@app.route('/')
def home(): return "Rajasinghe Bot v13 is Online!"

def run(): app.run(host='0.0.0.0', port=7860)
def keep_alive(): Thread(target=run).start()

# --- Configurations (කෙලින්ම ඇතුළත් කර ඇත) ---
# Janux, මෙතන තියෙන තොරතුරු නිවැරදිද කියලා ආයෙත් බලන්න
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
# @BotFather ගෙන් ගත්ත අලුත්ම Token එක මෙතන "" ඇතුළත දාන්න
MAIN_BOT_TOKEN = os.environ.get("MAIN_BOT_TOKEN", "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY")
DB_CHANNEL_ID = -1003750069060 

db_links = {} 
user_state = {}
registered_channels = {} 

bot = TelegramClient('rajasinghe_v13_session', API_ID, API_HASH)

# --- Database Sync ---
async def sync_database():
    try:
        async for message in bot.iter_messages(DB_CHANNEL_ID, limit=100):
            if message.text and "#DB_ENTRY" in message.text:
                data_str = message.text.split("DATA:")[1].strip()
                data = json.loads(data_str)
                db_links[data['link_id']] = data
        print("✅ Database Synced!")
    except: print("❌ Sync Error - Check if bot is Admin in Channel")

# --- Handlers ---
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        if link_id in db_links:
            data = db_links[link_id]
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 Password එක එවන්න:")
            await send_files(event.sender_id, link_id)
            return
    await event.respond("👑 **රාජසිංහ Ultimate Bot වැඩ!**\n\nලින්ක් එකක් හදන්න /link යවන්න.")

@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් ගොනු එවන්න. අවසන් වූ පසු **/done** එවන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        await event.respond(f"⚙️ Settings:\nFiles: {len(state['files'])}", 
        buttons=[[Button.inline("🔗 Generate Link", data="gen_final")]])

@bot.on(events.CallbackQuery(data="gen_final"))
async def callback(event):
    user_id = event.sender_id
    state = user_state.get(user_id)
    await event.edit("🔄 සකසමින් පවතියි...")
    saved_ids = []
    for m_id in state["files"]:
        m = await bot.forward_messages(DB_CHANNEL_ID, m_id, user_id)
        saved_ids.append(str(m.id))
    link_id = str(int(time.time()))
    link_data = {"link_id": link_id, "ids": "x".join(saved_ids), "password": state["pw"], "title": state["title"]}
    await bot.send_message(DB_CHANNEL_ID, f"#DB_ENTRY\nDATA:{json.dumps(link_data)}")
    db_links[link_id] = link_data
    url = f"https://t.me/{(await bot.get_me()).username}?start={link_id}"
    await event.edit(f"✅ ලින්ක් එක සාර්ථකයි:\n`{url}`")

async def send_files(user_id, link_key):
    data = db_links.get(link_key)
    msg_ids = [int(i) for i in data["ids"].split('x')]
    for m_id in msg_ids:
        await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)

async def main():
    keep_alive()
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    await sync_database()
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
