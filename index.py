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
def keep_alive(): Thread(target=run).start()

# --- Configurations ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8422828636:AAHA54LWg7qxqllIcQFKVjOHwHQL7x-K8qE"
DB_CHANNEL_ID = -1003750069060
ADMIN_ID = 443626880782 
FSUB_CHANNEL = "https://t.me/+Rktf3AlVNIkzMGNl" 

# Data Storage
user_storage = {}
user_state = {}
db_links = {} 
registered_channels = {} 
bot_stats = {"users": set(), "links_created": 0}
processed_msg_ids = set()

bot = TelegramClient('rajasinghe_final_v11', API_ID, API_HASH)

def is_duplicate(msg_id):
    if msg_id in processed_msg_ids: return True
    processed_msg_ids.add(msg_id)
    if len(processed_msg_ids) > 200: processed_msg_ids.pop()
    return False

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if is_duplicate(event.id): return
    bot_stats["users"].add(event.sender_id)
    
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        try:
            if FSUB_CHANNEL: await bot.get_permissions(FSUB_CHANNEL, event.sender_id)
        except:
            return await event.respond(f"❌ Join {FSUB_CHANNEL} first.", 
                                     buttons=[Button.url("Join", f"https://t.me/{FSUB_CHANNEL[1:]}")])

        if link_id in db_links:
            data = db_links[link_id]
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 Title: {data['title']}\nPassword එක ඇතුළත් කරන්න:")
        
        await send_files(event.sender_id, link_id)
        return
    await event.respond("👑 **රාජසිංහ Ultimate Bot**\n\n/link - ලින්ක් සෑදීමට\n/post - Post Schedule කිරීමට\n/stats - බොට්ගේ තොරතුරු")

# --- POST SCHEDULER COMMAND ---
@bot.on(events.NewMessage(pattern='/post'))
async def post_cmd(event):
    if is_duplicate(event.id): return
    user_id = event.sender_id
    if user_id not in registered_channels:
        user_state[user_id] = {"task": "register_channel"}
        return await event.respond("📢 මුලින්ම පෝස්ට් එක දාන්න ඕන චැනල් එකෙන් මැසේජ් එකක් මෙතනට **Forward** කරන්න.")
    
    user_state[user_id] = {"task": "post_text", "channel": registered_channels[user_id]}
    await event.respond("✅ දැන් පෝස්ට් එකට අවශ්‍ය **Text/Caption** එක එවන්න:")

# --- LINK COMMANDS ---
@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    if is_duplicate(event.id): return
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් ගොනු එවන්න. අවසන් වූ පසු **/done** එවන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        await event.respond(f"⚙️ **Link Settings:**\n\nFiles: {len(state['files'])}\nTitle: {state['title']}\nPassword: {state['pw']}", 
        buttons=[
            [Button.inline("🏷️ Set Title", data="set_title")],
            [Button.inline("🔐 Set Password", data="set_pw")],
            [Button.inline("🔗 Generate Link", data="gen_final")]
        ])

# --- MASTER MESSAGE HANDLER ---
@bot.on(events.NewMessage(incoming=True))
async def master_handler(event):
    if event.text.startswith('/'): return
    user_id = event.sender_id
    state = user_state.get(user_id)
    if not state: return

    # POST SCHEDULER WORKFLOW
    if state.get("task") == "register_channel":
        if event.fwd_from:
            # Channel ID එක ගන්න විදිහ Fix කරා
            if hasattr(event.fwd_from.from_id, 'channel_id'):
                registered_channels[user_id] = event.fwd_from.from_id.channel_id
                user_state[user_id] = None
                return await event.respond(f"✅ චැනල් එක රෙජිස්ටර් කළා! ID: {registered_channels[user_id]}\nදැන් නැවත /post ගසන්න.")
        await event.respond("❌ වැරදියි. කරුණාකර චැනල් එකේ පෝස්ට් එකක් **Forward** කරන්න.")

    elif state.get("task") == "post_text":
        state["post_text"] = event.text
        state["task"] = "post_btn"
        await event.respond("දැන් Button එකේ නම සහ Link එක මේ විදිහට එවන්න:\n`නම | URL` (උදා: Join | https://t.me/...)")

    elif state.get("task") == "post_btn":
        if "|" not in event.text: return await event.respond("❌ වැරදියි. `නම | URL` විදිහට එවන්න.")
        name, url = event.text.split("|", 1)
        state["btn_name"] = name.strip()
        state["btn_url"] = url.strip()
        state["task"] = "post_time"
        await event.respond("පෝස්ට් එක යවන්න ඕන වෙලාව එවන්න (YYYY-MM-DD HH:MM):\n`2026-03-02 21:00` (24h format එකෙන්)")

    elif state.get("task") == "post_time":
        try:
            target_time = datetime.strptime(event.text, '%Y-%m-%d %H:%M')
            delay = (target_time - datetime.now()).total_seconds()
            if delay < 0: return await event.respond("❌ අතීත කාලයක් දාන්න බැහැ. අලුත් වෙලාවක් එවන්න.")
            
            p_text = state["post_text"]
            p_chan = state["channel"]
            p_btn = [Button.url(state["btn_name"], state["btn_url"])]
            
            await event.respond(f"⏰ Post scheduled at {event.text} සාර්ථකයි!")
            user_state[user_id] = None
            
            await asyncio.sleep(delay)
            await bot.send_message(p_chan, p_text, buttons=p_btn)
        except Exception as e: 
            await event.respond(f"❌ Format වැරදියි: `YYYY-MM-DD HH:MM` ලෙස එවන්න. Error: {str(e)}")

    # LINK CREATION WORKFLOW
    elif state.get("task") == "setting_title":
        state["title"] = event.text
        state["task"] = None
        await event.respond(f"✅ Title සැකසුවා. දැන් /done එවන්න.")

    elif state.get("task") == "setting_pw":
        state["pw"] = event.text
        state["task"] = None
        await event.respond(f"✅ Password සැකසුවා. දැන් /done එවන්න.")

    elif state.get("mode") == "uploading":
        state["files"].append(event.message.id)
        await event.respond(f"✅ File {len(state['files'])} එකතු කළා.")

    elif state.get("task") == "verify_pw":
        link_id = state["link_id"]
        if event.text == db_links[link_id]['password']:
            await send_files(user_id, link_id)
            user_state[user_id] = None
        else: await event.respond("❌ වැරදි Password එකක්!")

# --- CALLBACKS ---
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    state = user_state.get(user_id)
    if not state: return

    if data == "set_title":
        state["task"] = "setting_title"
        await event.respond("🏷️ ලින්ක් එකට අවශ්‍ය නම (Title) එවන්න:")
    elif data == "set_pw":
        state["task"] = "setting_pw"
        await event.respond("🔐 අවශ්‍ය Password එක එවන්න:")
    elif data == "gen_final":
        await event.edit("🔄 Processing...")
        saved_ids = []
        for m_id in state["files"]:
            m = await bot.forward_messages(DB_CHANNEL_ID, m_id, user_id)
            saved_ids.append(str(m.id))
        
        link_id = str(int(time.time()))
        db_links[link_id] = {"ids": "x".join(saved_ids), "password": state["pw"], "title": state["title"]}
        bot_stats["links_created"] += 1
        url = f"https://t.me/{(await bot.get_me()).username}?start={link_id}"
        await event.edit(f"✅ **සාර්ථකයි!**\n\nLink: `{url}`")
        user_state[user_id] = None

async def send_files(user_id, link_key):
    data = db_links.get(link_key, {"ids": link_key})
    msg_ids = [int(i) for i in data["ids"].split('x')]
    await bot.send_message(user_id, "🛡️ Files එවමින් පවතියි...")
    for m_id in msg_ids:
        try: await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
        except: continue

async def main():
    keep_alive()
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ Final Fixed v11 Online!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
