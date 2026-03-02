import asyncio
import time
from telethon import TelegramClient, events, Button

# --- බොට්ගේ විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
# Double Message පාලනය (Deduplication)
processed_msg_ids = set()

bot = TelegramClient('rajasinghe_ultra_fixed', API_ID, API_HASH)

def is_duplicate(msg_id):
    """පණිවිඩය දැනටමත් process කර ඇත්දැයි බලයි"""
    if msg_id in processed_msg_ids:
        return True
    processed_msg_ids.add(msg_id)
    # මතකය පිරීම වැළැක්වීමට පැරණි ඒවා අයින් කිරීම
    if len(processed_msg_ids) > 100:
        # පළමු එක ඉවත් කිරීම (FIFO)
        processed_msg_ids.remove(next(iter(processed_msg_ids)))
    return False

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if is_duplicate(event.id): return
    
    if len(event.message.text.split()) > 1:
        msg_ids = [int(i) for i in event.message.text.split()[1].split('x')]
        await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
        for m_id in msg_ids:
            try: await bot.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
            except: continue
        return
    await event.respond(f"ආයුබෝවන් Boss! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න `/link` එවන්න.")

@bot.on(events.NewMessage(pattern='/link'))
async def link_handler(event):
    if is_duplicate(event.id): return
    user_id = event.sender_id
    user_state[user_id] = "uploading"
    user_storage[user_id] = []
    await event.respond("✅ දැන් මට share කරන්න ඕන files/messages එවන්න. අවසන් වූ පසු 'Generate' ඔබන්න.")

@bot.on(events.NewMessage(incoming=True))
async def collector_handler(event):
    if event.text.startswith('/'): return
    user_id = event.sender_id
    
    if user_state.get(user_id) == "uploading":
        if is_duplicate(event.id): return
        
        user_storage[user_id].append(event.message.id)
        count = len(user_storage[user_id])
        buttons = [[Button.inline("තව තියෙනවා ➕", data="add_more")],
                   [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]]
        await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    if event.data == b"add_more":
        await event.answer("හරි, තව එවන්න!")
    elif event.data == b"gen_link":
        if not user_storage.get(user_id): return await event.answer("කලින් file එකක් එවන්න!", alert=True)

        await event.edit("🔄 ලින්ක් එක සකසමින්...")
        saved_ids = [str((await bot.forward_messages(DB_CHANNEL_ID, m, user_id)).id) for m in user_storage[user_id]]
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={'x'.join(saved_ids)}"
        await event.edit(f"✅ **සාර්ථකයි!**\n\n`{link}`")
        user_storage[user_id] = []; user_state[user_id] = None

# --- Main Run ---
async def main():
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ සම්පූර්ණයෙන්ම සූදානම්!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
