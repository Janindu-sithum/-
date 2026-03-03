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
processed_messages = set()
# මේ Lock එක මගින් එකවර එක මැසේජ් එකක් පමණක් process කරන බව තහවුරු කරයි
message_lock = asyncio.Lock()

async def check_duplicate(msg_id):
    async with message_lock:
        if msg_id in processed_messages:
            return True
        processed_messages.add(msg_id)
        # පරණ මැසේජ් 1000කට වඩා තිබේ නම් අයින් කරන්න
        if len(processed_messages) > 1000:
            processed_messages.clear()
        return False

# Data Storage
user_state = {}
db_links = {} 
registered_channels = {} 
bot_stats = {"users": set(), "links_created": 0}

bot = TelegramClient('rajasinghe_final_v13', API_ID, API_HASH)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if await check_duplicate(event.id): return
    bot_stats["users"].add(event.sender_id)
    
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        
        try:
            await bot.get_permissions(FSUB_CHANNEL, event.sender_id)
        except Exception:
            return await event.respond("❌ කරුණාකර චැනල් එකට සම්බන්ධ වී නැවත උත්සාහ කරන්න.", 
                                     buttons=[Button.url("Join Channel", FSUB_CHANNEL)])

        if link_id in db_links:
            data = db_links[link_id]
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 **Title:** {data['title']}\n\nPassword එවන්න:")
            await send_files(event.sender_id, link_id)
            return
            
    await event.respond("👑 **රාජසිංහ Ultimate Bot**\n\n/link - ලින්ක් සෑදීමට\n/post - Post Schedule කිරීමට")

@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    if await check_duplicate(event.id): return
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් ගොනු එවන්න. අවසන් වූ පසු **/done** එවන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    if await check_duplicate(event.id): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        if not state['files']:
            return await event.respond("❌ කිසිදු ගොනුවක් නැත.")
            
        await event.respond(
            f"⚙️ **Link Settings:**\n\n📂 Files: {len(state['files'])}\n🏷️ Title: {state['title']}\n🔐 Password: {state['pw']}", 
            buttons=[
                [Button.inline("🏷️ Set Title", data="set_title"), Button.inline("🔐 Set Password", data="set_pw")],
                [Button.inline("🔗 Generate Link", data="gen_final")]
            ]
        )

@bot.on(events.NewMessage(incoming=True))
async def master_handler(event):
    if event.text.startswith('/') or await check_duplicate(event.id): return
    
    user_id = event.sender_id
    state = user_state.get(user_id)
    if not state: return

    # File Uploading
    if state.get("mode") == "uploading" and not state.get("task"):
        state["files"].append(event.message.id)
        return 

    # Settings
    elif state.get("task") == "setting_title":
        state["title"] = event.text
        state["task"] = None
        await event.respond("✅ Title එක සැකසුවා. දැන් /done එවන්න.")

    elif state.get("task") == "setting_pw":
        state["pw"] = event.text
        state["task"] = None
        await event.respond("✅ Password එක සැකසුවා. දැන් /done එවන්න.")

    # Password Check
    elif state.get("task") == "verify_pw":
        link_id = state["link_id"]
        if event.text == db_links[link_id]['password']:
            await send_files(user_id, link_id)
            user_state[user_id] = None
        else:
            await event.respond("❌ වැරදි Password එකක්!")

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    state = user_state.get(user_id)
    if not state: return

    if data == "set_title":
        state["task"] = "setting_title"
        await event.respond("🏷️ Title එක එවන්න:")
    elif data == "set_pw":
        state["task"] = "setting_pw"
        await event.respond("🔐 Password එක එවන්න:")
    elif data == "gen_final":
        await event.edit("🔄 Processing...")
        saved_ids = []
        for m_id in state["files"]:
            m = await bot.forward_messages(DB_CHANNEL_ID, m_id, user_id)
            saved_ids.append(str(m.id))
        
        link_id = str(int(time.time()))
        db_links[link_id] = {"ids": "x".join(saved_ids), "password": state["pw"], "title": state["title"]}
        bot_username = (await bot.get_me()).username
        url = f"https://t.me/{bot_username}?start={link_id}"
        await event.edit(f"✅ **සාර්ථකයි!**\n\nLink: `{url}`")
        user_state[user_id] = None

async def send_files(user_id, link_key):
    data = db_links.get(link_key)
    if not data: return
    msg_ids = [int(i) for i in data["ids"].split('x')]
    await bot.send_message(user_id, "🛡️ Files එවමින් පවතියි...")
    for m_id in msg_ids:
        try:
            await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
            await asyncio.sleep(1) # වැදගත්: වේගය පාලනයට
        except: continue

async def main():
    keep_alive()
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("Anti-Spam Version Online!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
