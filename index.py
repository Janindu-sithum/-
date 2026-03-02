import asyncio
from telethon import TelegramClient, events, Button

# --- Bot Settings ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
# ඔයා දුන්න අලුත් Token එක
MAIN_BOT_TOKEN = "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
# Double message වැළැක්වීමේ පාලකය
processed_msgs = set()

bot = TelegramClient('rajasinghe_ultra_fixed', API_ID, API_HASH)

def is_duplicate(msg_id):
    """පණිවිඩය දැනටමත් process කර ඇත්දැයි පරීක්ෂා කරයි"""
    if msg_id in processed_msgs:
        return True
    processed_msgs.add(msg_id)
    # මතකය පිරී යාම වැළැක්වීමට පැරණි IDs අයින් කිරීම
    if len(processed_msgs) > 1000:
        processed_msgs.pop()
    return False

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if is_duplicate(event.id): return

    if len(event.message.text.split()) > 1:
        msg_ids_raw = event.message.text.split()[1]
        msg_ids = [int(i) for i in msg_ids_raw.split('x')]
        await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
        for m_id in msg_ids:
            try: await bot.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
            except: continue
        return
    
    await event.respond(f"ආයුබෝවන් {event.sender.first_name}! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න අවශ්‍ය නම් `/link` ලෙස type කරන්න.")

@bot.on(events.NewMessage(pattern='/link'))
async def link_handler(event):
    if is_duplicate(event.id): return

    user_id = event.sender_id
    user_state[user_id] = "uploading"
    user_storage[user_id] = []
    await event.respond("✅ දැන් ඔයාට share කරන්න ඕන files/messages මට එවන්න. ඒවා අවසන් වූ පසු 'Generate Link' බොත්තම ඔබන්න.")

@bot.on(events.NewMessage(pattern='/clone'))
async def clone_handler(event):
    if is_duplicate(event.id): return
    
    args = event.message.text.split()
    if len(args) < 2:
        return await event.respond("භාවිතය: `/clone BOT_TOKEN_HERE`")
    
    token = args[1]
    await event.respond("🔄 අලුත් Bot පණගන්වමින් පවතියි...")
    try:
        new_bot = TelegramClient(f"bot_{token[:8]}", API_ID, API_HASH)
        await new_bot.start(bot_token=token)
        # Register same logic to cloned bot
        setup_additional_handlers(new_bot)
        await event.respond("✅ සාර්ථකයි! අලුත් Bot දැන් ක්‍රියාත්මකයි.")
    except Exception as e:
        await event.respond(f"❌ වැරදීමක්: {str(e)}")

@bot.on(events.NewMessage(incoming=True))
async def file_handler(event):
    # Command එකක් නම් handle නොකරන්න
    if event.text.startswith('/'): return
    
    user_id = event.sender_id
    if user_state.get(user_id) == "uploading":
        if is_duplicate(event.id): return
        
        user_storage[user_id].append(event.message.id)
        count = len(user_storage[user_id])
        
        buttons = [
            [Button.inline("තව තියෙනවා ➕", data="add_more")],
            [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]
        ]
        await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})\nතව එවන්නද?", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    
    if event.data == b"add_more":
        await event.answer("හරි, තව එවන්න. මම බලාගෙන ඉන්නේ!")
    
    elif event.data == b"gen_link":
        if not user_storage.get(user_id):
            return await event.answer("කරුණාකර කලින් file එකක් එවන්න!", alert=True)

        await event.edit("🔄 ලින්ක් එක සකසමින් පවතියි, කරුණාකර රැඳී සිටින්න...")
        
        saved_ids = []
        for msg_id in user_storage[user_id]:
            sent_msg = await bot.forward_messages(DB_CHANNEL_ID, msg_id, user_id)
            saved_ids.append(str(sent_msg.id))
        
        unique_string = "x".join(saved_ids)
        me = await bot.get_me()
        share_link = f"https://t.me/{me.username}?start={unique_string}"
        
        await event.edit(f"✅ **සාර්ථකයි!**\n\nමෙන්න ඔයාගේ ලින්ක් එක:\n`{share_link}`")
        
        # Reset storage
        user_storage[user_id] = []
        user_state[user_id] = None

def setup_additional_handlers(client):
    # මේක පාවිච්චි කරන්නේ Clone කරන බෝට්ලාටත් මේ logic එකම දාන්නයි
    client.add_event_handler(start_handler, events.NewMessage(pattern='/start'))
    client.add_event_handler(link_handler, events.NewMessage(pattern='/link'))
    client.add_event_handler(file_handler, events.NewMessage(incoming=True))
    client.add_event_handler(callback_handler, events.CallbackQuery)

async def main():
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ Ultra-Fixed පණගැන්වුණා...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
