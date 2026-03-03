import asyncio
import time
from datetime import datetime
from telethon import TelegramClient, events, Button, errors
from flask import Flask
from threading import Thread

# --- Flask Server (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Rajasinghe Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run, daemon=True).start()

# --- Configurations ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8422828636:AAHA54LWg7qxqllIcQFKVjOHwHQL7x-K8qE"
DB_CHANNEL_ID = -1003750069060
FSUB_CHANNEL = "https://t.me/+Rktf3AlVNIkzMGNl" 

# --- Anti-Duplicate System ---
recent_messages = {}

def is_duplicate_request(msg_id):
    now = time.time()
    if msg_id in recent_messages:
        if now - recent_messages[msg_id] < 5: # තත්පර 5ක limit එකක්
            return True
    recent_messages[msg_id] = now
    if len(recent_messages) > 1000: recent_messages.clear()
    return False

# Data Storage
user_state = {}
db_links = {} 
bot_stats = {"users": set()}

# Session නම වෙනස් කළා අලුතින් connect වෙන්න
bot = TelegramClient('rajasinghe_final_v15', API_ID, API_HASH)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if is_duplicate_request(event.id): return
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        try:
            await bot.get_permissions(FSUB_CHANNEL, event.sender_id)
        except:
            return await event.respond("❌ කරුණාකර චැනල් එකට Join වෙන්න.", 
                                     buttons=[Button.url("Join Channel", FSUB_CHANNEL)])
        
        if link_id in db_links:
            data = db_links[link_id]
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 **Title:** {data['title']}\nPassword එවන්න:")
            await send_files(event.sender_id, link_id)
            return
    await event.respond("👑 **රාජසිංහ Ultimate Bot**\n\n/link - ලින්ක් සෑදීමට")

@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    if is_duplicate_request(event.id): return
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් ගොනු එවන්න. අවසන් වූ පසු **/done** එවන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    if is_duplicate_request(event.id): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        await event.respond(
            f"⚙️ **Settings:**\nFiles: {len(state['files'])}\nTitle: {state['title']}", 
            buttons=[[Button.inline("🔗 Generate Link", data="gen_final")]]
        )

@bot.on(events.NewMessage(incoming=True))
async def master_handler(event):
    if event.text.startswith('/') or is_duplicate_request(event.id): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        state["files"].append(event.message.id)

@bot.on(events.CallbackQuery(data="gen_final"))
async def gen_callback(event):
    state = user_state.get(event.sender_id)
    if not state: return
    await event.edit("🔄 Processing...")
    saved_ids = []
    for m_id in state["files"]:
        m = await bot.forward_messages(DB_CHANNEL_ID, m_id, event.sender_id)
        saved_ids.append(str(m.id))
    
    link_id = str(int(time.time()))
    db_links[link_id] = {"ids": "x".join(saved_ids), "title": state["title"]}
    bot_u = (await bot.get_me()).username
    await event.edit(f"✅ Link: `https://t.me/{bot_u}?start={link_id}`")
    user_state[event.sender_id] = None

async def send_files(user_id, link_key):
    data = db_links.get(link_key)
    msg_ids = [int(i) for i in data["ids"].split('x')]
    for m_id in msg_ids:
        await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
        await asyncio.sleep(1)

async def main():
    keep_alive()
    # bot.start() වෙනුවට මේ විදිහට පාවිච්චි කරන්න
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("Bot is fully fixed and online!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
