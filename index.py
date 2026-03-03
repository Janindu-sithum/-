import asyncio
import time
from datetime import datetime
from telethon import TelegramClient, events, Button, errors
from flask import Flask
from threading import Thread

# --- Flask Server (Keep Alive) ---
app = Flask('')

@app.route('/')
def home(): 
    return "Rajasinghe Bot is Online!"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive(): 
    Thread(target=run, daemon=True).start()

# --- Configurations ---
# Janux, ඔයාගේ Firebase විස්තර මම මෙතනට දැම්මේ නැහැ, ආරක්ෂාවට. 
# මේ Tokens ටික එහෙම්මම තියෙන්න දෙන්න.
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8422828636:AAHA54LWg7qxqllIcQFKVjOHwHQL7x-K8qE"
DB_CHANNEL_ID = -1003750069060
ADMIN_ID = 443626880782 
FSUB_CHANNEL = "https://t.me/+Rktf3AlVNIkzMGNl" 

# Data Storage
user_state = {}
db_links = {} 
registered_channels = {} 
bot_stats = {"users": set(), "links_created": 0}
processed_msg_ids = set()

bot = TelegramClient('rajasinghe_final_v11', API_ID, API_HASH)

def is_duplicate(msg_id):
    if msg_id in processed_msg_ids: return True
    processed_msg_ids.add(msg_id)
    if len(processed_msg_ids) > 500: processed_msg_ids.clear()
    return False

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if is_duplicate(event.id): return
    bot_stats["users"].add(event.sender_id)
    
    # Deep linking check
    if len(event.message.text.split()) > 1:
        link_id = event.message.text.split()[1]
        
        # F-Sub Check
        try:
            # Note: link එකේ තියෙන +Rktf... කොටසින් check කිරීම අපහසුයි ID එක නැතුව.
            # මෙතන සරලව user channel එකේ ඉන්නවද කියලා බලනවා.
            await bot.get_permissions(FSUB_CHANNEL, event.sender_id)
        except Exception:
            return await event.respond(f"❌ ඔබට මෙම ගොනු ලබා ගැනීමට නම් අපගේ චැනල් එකට සම්බන්ධ විය යුතුය.", 
                                     buttons=[Button.url("Join Channel", FSUB_CHANNEL)])

        if link_id in db_links:
            data = db_links[link_id]
            if data.get('password'):
                user_state[event.sender_id] = {"task": "verify_pw", "link_id": link_id}
                return await event.respond(f"🔐 **Title:** {data['title']}\n\nකරුණාකර මෙම ගොනු සඳහා වන Password එක ඇතුළත් කරන්න:")
        
            await send_files(event.sender_id, link_id)
            return
            
    await event.respond("👑 **රාජසිංහ Ultimate Bot**\n\nමෙම බොට් මගින් ඔබට File Store ලින්ක් සෑදීමට සහ Posts Schedule කිරීමට හැක.\n\n/link - ලින්ක් සෑදීමට\n/post - Post Schedule කිරීමට\n/stats - බොට්ගේ තොරතුරු")

@bot.on(events.NewMessage(pattern='/post'))
async def post_cmd(event):
    if is_duplicate(event.id): return
    user_id = event.sender_id
    if user_id not in registered_channels:
        user_state[user_id] = {"task": "register_channel"}
        return await event.respond("📢 මුලින්ම පෝස්ට් එක දාන්න ඕන චැනල් එකෙන් මැසේජ් එකක් මෙතනට **Forward** කරන්න.")
    
    user_state[user_id] = {"task": "post_text", "channel": registered_channels[user_id]}
    await event.respond("✅ දැන් පෝස්ට් එකට අවශ්‍ය **Text/Caption** එක එවන්න:")

@bot.on(events.NewMessage(pattern='/link'))
async def link_cmd(event):
    if is_duplicate(event.id): return
    user_state[event.sender_id] = {"mode": "uploading", "files": [], "title": "No Title", "pw": None}
    await event.respond("✅ දැන් ගොනු එකින් එක එවන්න. සියල්ල එවා අවසන් වූ පසු **/done** ලෙස type කරන්න.")

@bot.on(events.NewMessage(pattern='/done'))
async def done_cmd(event):
    user_id = event.sender_id
    state = user_state.get(user_id)
    if state and state.get("mode") == "uploading":
        if not state['files']:
            return await event.respond("❌ ඔබ කිසිදු ගොනුවක් එවා නැත.")
            
        await event.respond(
            f"⚙️ **Link Settings:**\n\n📂 Files: {len(state['files'])}\n🏷️ Title: {state['title']}\n🔐 Password: {state['pw'] if state['pw'] else 'None'}", 
            buttons=[
                [Button.inline("🏷️ Set Title", data="set_title")],
                [Button.inline("🔐 Set Password", data="set_pw")],
                [Button.inline("🔗 Generate Link", data="gen_final")]
            ]
        )

@bot.on(events.NewMessage(incoming=True))
async def master_handler(event):
    # Command එකක් නම් ignore කරන්න
    if event.text.startswith('/'): return
    
    user_id = event.sender_id
    state = user_state.get(user_id)
    if not state: return

    # POST SCHEDULER
    if state.get("task") == "register_channel":
        if event.fwd_from:
            try:
                # Forward කළ message එකෙන් Channel ID එක ගැනීම
                channel_id = event.fwd_from.from_id.channel_id
                registered_channels[user_id] = channel_id
                user_state[user_id] = None
                return await event.respond(f"✅ චැනල් එක සාර්ථකව සම්බන්ධ කළා!\nID: `{channel_id}`\nදැන් නැවත /post ගසන්න.")
            except:
                pass
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
        await event.respond("පෝස්ට් එක යවන්න ඕන වෙලාව එවන්න (YYYY-MM-DD HH:MM):\n`2026-03-10 21:00` (24h format)")

    elif state.get("task") == "post_time":
        try:
            target_time = datetime.strptime(event.text, '%Y-%m-%d %H:%M')
            delay = (target_time - datetime.now()).total_seconds()
            if delay < 0: return await event.respond("❌ අතීත කාලයක් ලබා දිය නොහැක.")
            
            p_text = state["post_text"]
            p_chan = state["channel"]
            p_btn = [Button.url(state["btn_name"], state["btn_url"])]
            
            await event.respond(f"⏰ පෝස්ට් එක {event.text} ට Schedule කළා.")
            user_state[user_id] = None
            
            await asyncio.sleep(delay)
            await bot.send_message(p_chan, p_text, buttons=p_btn)
        except:
            await event.respond("❌ Format වැරදියි. `YYYY-MM-DD HH:MM` ලෙස එවන්න.")

    # LINK CREATION
    elif state.get("task") == "setting_title":
        state["title"] = event.text
        state["task"] = None
        await event.respond(f"✅ Title එක සැකසුවා. දැන් නැවත **/done** එවන්න.")

    elif state.get("task") == "setting_pw":
        state["pw"] = event.text
        state["task"] = None
        await event.respond(f"✅ Password එක සැකසුවා. දැන් නැවත **/done** එවන්න.")

    elif state.get("mode") == "uploading":
        state["files"].append(event.message.id)
        # ගොනු ගණන පෙන්වීමට respond එකක් දීම කරදරයක් නම් මේක අයින් කරන්න පුළුවන්
        # await event.respond(f"✅ File {len(state['files'])} එකතු කළා.")

    elif state.get("task") == "verify_pw":
        link_id = state["link_id"]
        if event.text == db_links[link_id]['password']:
            await send_files(user_id, link_id)
            user_state[user_id] = None
        else: 
            await event.respond("❌ වැරදි Password එකක්! නැවත උත්සාහ කරන්න.")

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
        await event.edit("🔄 Processing... Please wait.")
        saved_ids = []
        for m_id in state["files"]:
            m = await bot.forward_messages(DB_CHANNEL_ID, m_id, user_id)
            saved_ids.append(str(m.id))
        
        link_id = str(int(time.time()))
        db_links[link_id] = {"ids": "x".join(saved_ids), "password": state["pw"], "title": state["title"]}
        bot_stats["links_created"] += 1
        
        me = await bot.get_me()
        url = f"https://t.me/{me.username}?start={link_id}"
        await event.edit(f"✅ **සාර්ථකව ලින්ක් එක නිර්මාණය කළා!**\n\nLink: `{url}`", buttons=[Button.url("Open Link", url)])
        user_state[user_id] = None

async def send_files(user_id, link_key):
    data = db_links.get(link_key)
    if not data: return
    
    msg_ids = [int(i) for i in data["ids"].split('x')]
    await bot.send_message(user_id, f"🛡️ **{data['title']}** අදාළ ගොනු එවමින් පවතියි...")
    for m_id in msg_ids:
        try: 
            await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
            await asyncio.sleep(1) # Flood wait මග හරවා ගැනීමට
        except: 
            continue

async def main():
    keep_alive()
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ Bot is Online!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
