import asyncio
from telethon import TelegramClient, events, Button

# --- බොට්ගේ විස්තර (ජනුක්ස්ගේ දත්ත) ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
# අලුත්ම Token එක මෙතනට දාන්න
MAIN_BOT_TOKEN = "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
# මෙලෙස කිරීමෙන් එකම පණිවිඩය දෙපාරක් process වීම නවතී
processed_messages = set()

bot = TelegramClient('rajasinghe_railway', API_ID, API_HASH)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    # පණිවිඩය දැනටමත් process කර ඇත්නම් අත්හරින්න
    if event.id in processed_messages: return
    processed_messages.add(event.id)

    if len(event.message.text.split()) > 1:
        msg_ids = [int(i) for i in event.message.text.split()[1].split('x')]
        await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
        for m_id in msg_ids:
            try: await bot.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
            except: continue
        return
    await event.respond(f"ආයුබෝවන්! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න `/link` එවන්න.")

@bot.on(events.NewMessage(pattern='/link'))
async def link_handler(event):
    if event.id in processed_messages: return
    processed_messages.add(event.id)

    user_id = event.sender_id
    user_state[user_id] = "uploading"
    user_storage[user_id] = []
    await event.respond("✅ දැන් මට ඕනෑම දෙයක් එවන්න. අවසන් වූ පසු 'Generate' ඔබන්න.")

@bot.on(events.NewMessage(incoming=True))
async def file_handler(event):
    user_id = event.sender_id
    # Railway වලදී double trigger වීම වැළැක්වීමට
    if event.id in processed_messages: return
    
    if not event.text.startswith('/') and user_state.get(user_id) == "uploading":
        processed_messages.add(event.id)
        user_storage[user_id].append(event.message.id)
        count = len(user_storage[user_id])
        
        buttons = [[Button.inline("තව තියෙනවා ➕", data="add_more")],
                   [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]]
        await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})\nතව එවන්නද?", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    if event.data == b"add_more":
        await event.answer("හරි, තව එවන්න!")
    elif event.data == b"gen_link":
        if not user_storage.get(user_id):
            return await event.answer("කලින් file එකක් එවන්න!", alert=True)

        await event.edit("🔄 ලින්ක් එක සකසමින්...")
        saved_ids = [str((await bot.forward_messages(DB_CHANNEL_ID, m, user_id)).id) for m in user_storage[user_id]]
        
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={'x'.join(saved_ids)}"
        await event.edit(f"✅ **සාර්ථකයි!**\n\nමෙන්න ලින්ක් එක:\n`{link}`")
        user_storage[user_id] = []; user_state[user_id] = None

# --- Main Run ---
async def main():
    # Session එක පිරිසිදු කර ආරම්භ කිරීම
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ Railway මත සාර්ථකව ක්‍රියාත්මකයි...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # ලැයිස්තුව පිරිසිදු කර තැබීමට
    asyncio.run(main())
