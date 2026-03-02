import asyncio
import logging
from telethon import TelegramClient, events, Button

# --- බොට්ගේ විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
# පණිවිඩ දෙපාරක් එන එක නවත්වන ලැයිස්තුව
processed_msg_ids = set()

# Client එක ආරම්භ කිරීම
bot = TelegramClient('rajasinghe_final_v3', API_ID, API_HASH)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    # පණිවිඩය දැනටමත් process කර ඇත්නම් අත්හරින්න
    if event.id in processed_msg_ids: return
    processed_msg_ids.add(event.id)

    # File retrieval (ලින්ක් එකක් හරහා ආවොත්)
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
    if event.id in processed_msg_ids: return
    processed_msg_ids.add(event.id)

    user_id = event.sender_id
    user_state[user_id] = "uploading"
    user_storage[user_id] = []
    await event.respond("✅ දැන් මට share කරන්න ඕන files/messages එවන්න. අවසන් වූ පසු 'Generate' බොත්තම ඔබන්න.")

@bot.on(events.NewMessage(incoming=True))
async def collector_handler(event):
    # Command එකක් නම් මෙය මගහරින්න
    if event.text.startswith('/'): return
    
    user_id = event.sender_id
    if user_state.get(user_id) == "uploading":
        # Double message filter
        if event.id in processed_msg_ids: return
        processed_msg_ids.add(event.id)

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
            return await event.answer("කරුණාකර කලින් file එකක් එවන්න!", alert=True)

        await event.edit("🔄 ලින්ක් එක සකසමින් පවතියි...")
        
        saved_ids = []
        for msg_id in user_storage[user_id]:
            # DB Channel එකට forward කර එහි ID එක ලබා ගැනීම
            sent_msg = await bot.forward_messages(DB_CHANNEL_ID, msg_id, user_id)
            saved_ids.append(str(sent_msg.id))
        
        unique_string = "x".join(saved_ids)
        me = await bot.get_me()
        share_link = f"https://t.me/{me.username}?start={unique_string}"
        
        await event.edit(f"✅ **සාර්ථකයි!**\n\nමෙන්න ඔයාගේ ලින්ක් එක:\n`{share_link}`")
        
        # දත්ත Reset කිරීම
        user_storage[user_id] = []
        user_state[user_id] = None

# --- Main Run ---
async def main():
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ Bot සාර්ථකව පණ ගැන්වුණා!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
