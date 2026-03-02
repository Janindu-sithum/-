import asyncio
from telethon import TelegramClient, events, Button

# --- බොට්ගේ විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
BOT_TOKEN = "8302327984:AAFa4iJBJiYeQm1acQi1Z3uTHj4i_crlJ_c"
DB_CHANNEL_ID = -1003750069060

# Client එක සාදමු (No Proxy needed for Koyeb/Render)
bot = TelegramClient('rajasinghe_session', API_ID, API_HASH)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    # ලින්ක් එකක් හරහා ආවොත්
    if len(event.message.text.split()) > 1:
        msg_ids_raw = event.message.text.split()[1]
        msg_ids = [int(i) for i in msg_ids_raw.split('x')]
        await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
        for m_id in msg_ids:
            try:
                await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
            except Exception as e:
                print(f"Error forwarding: {e}")
        return

    welcome_msg = (
        f"ආයුබෝවන් {event.sender.first_name}! මම රාජසිංහ. 👑\n\n"
        "ඔයාට share කරන්න ඕන ඕනෑම දෙයක් මට එවන්න.\n"
        "වැඩේ ඉවර වුණාම මම ඔයාට රහස්‍ය ලින්ක් එකක් දෙන්නම්."
    )
    await event.respond(welcome_msg)

@bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and not e.text.startswith('/')))
async def handle_incoming(event):
    if not hasattr(bot, 'user_storage'):
        bot.user_storage = {}
        
    user_id = event.sender_id
    if user_id not in bot.user_storage:
        bot.user_storage[user_id] = []
    
    bot.user_storage[user_id].append(event.message.id)
    count = len(bot.user_storage[user_id])
    
    buttons = [
        [Button.inline("තව තියෙනවා ➕", data="add_more")],
        [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]
    ]
    await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})\nතව එවනවද?", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    if event.data == b"add_more":
        await event.answer("හරි, තව එවන්න!")
    elif event.data == b"gen_link":
        if user_id not in bot.user_storage or not bot.user_storage[user_id]:
            await event.answer("කරුණාකර කලින් file එකක් එවන්න!", alert=True)
            return

        await event.edit("🔄 ලින්ක් එක සකසමින් පවතියි...")
        saved_ids = []
        for msg_id in bot.user_storage[user_id]:
            sent_msg = await bot.forward_messages(DB_CHANNEL_ID, msg_id, user_id)
            saved_ids.append(str(sent_msg.id))
        
        unique_string = "x".join(saved_ids)
        bot_info = await bot.get_me()
        share_link = f"https://t.me/{bot_info.username}?start={unique_string}"
        
        await event.edit(f"✅ **සාර්ථකයි!**\n\nමෙන්න ඔයාගේ ලින්ක් එක:\n`{share_link}`")
        bot.user_storage[user_id] = []

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("රාජසිංහ සාර්ථකව පණ ගැන්වුණා!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
