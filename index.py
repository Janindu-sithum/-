import asyncio
import time
import os
from datetime import datetime
from telethon import TelegramClient, events, Button, errors
from flask import Flask
from threading import Thread

# --- Flask Server for Railway Port Binding ---
app = Flask('')
@app.route('/')
def home(): return "Rajasinghe Bot is Online!"

def run():
    # Railway එකෙන් දෙන PORT එක පාවිච්චි කිරීම
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# --- Configurations ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
# ⚠️ Janux, පුළුවන් නම් අලුත් Bot Token එකක් අරන් දාන්න.
MAIN_BOT_TOKEN = "8422828636:AAHA54LWg7qxqllIcQFKVjOHwHQL7x-K8qE"
DB_CHANNEL_ID = -1003750069060
FSUB_CHANNEL = "https://t.me/+Rktf3AlVNIkzMGNl"

# --- Anti-Duplicate (Universal) ---
# Railway instances කිහිපයක් තිබුණත් වැඩ කරන ලෙස මෙය සැකසූවෙමි
processed_cache = {}

async def is_duplicate(msg_id):
    now = time.time()
    if msg_id in processed_cache:
        return True
    processed_cache[msg_id] = now
    # පරණ cache එක අයින් කිරීම
    if len(processed_cache) > 500:
        processed_cache.clear()
    return False

# Data Storage
user_state = {}
db_links = {} 

# Session නම වෙනස් කිරීම අනිවාර්යයි
bot = TelegramClient('railway_rajasinghe_v16', API_ID, API_HASH, 
                     connection_retries=None, 
                     auto_reconnect=True)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if await is_duplicate(event.id): return
    
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        try:
            await bot.get_permissions(FSUB_CHANNEL, event.sender_id)
        except:
            return await event.respond("❌ කරුණාකර චැනල් එකට සම්බන්ධ වන්න.", 
                                     buttons=[Button.url("Join Channel", FSUB_CHANNEL)])
        
        if link_id in db_links:
            data = db_links[link_id]
            # Password check එක තිබේ නම්
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 **{data['title']}** සඳහා Password එවන්න:")
            await send_files(event.sender_id, link_id)
            return

    await event.respond("👑 **රාජසිංහ Ultimate Bot (Railway Fix)**\n\n/link - ලින්ක් සෑදීමට")

@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    if await is_duplicate(event.id): return
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් Files එවන්න. අවසන් වූ පසු **/done** එවන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    if await is_duplicate(event.id): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        if not state['files']: return await event.respond("❌ Files නැත.")
        await event.respond(
            f"⚙️ **Settings:**\nFiles: {len(state['files'])}\nTitle: {state['title']}", 
            buttons=[
                [Button.inline("🏷️ Set Title", data="set_title")],
                [Button.inline("🔗 Generate Link", data="gen_final")]
            ]
        )

@bot.on(events.NewMessage(incoming=True))
async def master_handler(event):
    if event.text.startswith('/') or await is_duplicate(event.id): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if not state: return

    if state.get("mode") == "uploading":
        state["files"].append(event.message.id)
    elif state.get("task") == "setting_title":
        state["title"] = event.text
        state["task"] = None
        await event.respond("✅ Title එක සැකසුවා. දැන් /done එවන්න.")

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    state = user_state.get(user_id)
    if not state: return

    if data == "set_title":
        state["task"] = "setting_title"
        await event.respond("🏷️ Title එවන්න:")
    elif data == "gen_final":
        await event.edit("🔄 Processing... (Railway වලදී මදක් ප්‍රමාද විය හැක)")
        saved_ids = []
        for m_id in state["files"]:
            try:
                m = await bot.forward_messages(DB_CHANNEL_ID, m_id, user_id)
                saved_ids.append(str(m.id))
            except: continue
        
        link_id = str(int(time.time()))
        db_links[link_id] = {"ids": "x".join(saved_ids), "title": state["title"]}
        bot_u = (await bot.get_me()).username
        await event.edit(f"✅ ලින්ක් එක සාර්ථකයි:\n`https://t.me/{bot_u}?start={link_id}`")
        user_state[user_id] = None

async def send_files(user_id, link_key):
    data = db_links.get(link_key)
    msg_ids = [int(i) for i in data["ids"].split('x')]
    await bot.send_message(user_id, "🛡️ Files එවමින් පවතියි...")
    for m_id in msg_ids:
        try:
            await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
            await asyncio.sleep(1.5)
        except: continue

async def main():
    keep_alive()
    print("Railway Deployment Starting...")
    try:
        await bot.start(bot_token=MAIN_BOT_TOKEN)
        print("✅ Connection Established!")
        await bot.run_until_disconnected()
    except errors.FloodWaitError as e:
        print(f"❌ FloodWait: {e.seconds} seconds. Waiting...")
        await asyncio.sleep(e.seconds)
        await main()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
