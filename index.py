import asyncio
from telethon import TelegramClient, events, Button

# --- මූලික විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8302327984:AAFa4iJBJiYeQm1acQi1Z3uTHj4i_crlJ_c"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}

# Client එක මෙතනදී සාදමු
bot = TelegramClient('rajasinghe_main', API_ID, API_HASH)

# --- Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    if len(event.message.text.split()) > 1:
        msg_ids_raw = event.message.text.split()[1]
        msg_ids = [int(i) for i in msg_ids_raw.split('x')]
        await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
        for m_id in msg_ids:
            try: await bot.forward_messages(user_id, m_id, DB_CHANNEL_ID)
            except: continue
        return
    await event.respond(f"ආයුබෝවන් {event.sender.first_name}! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න `/link` එවන්න.")

@bot.on(events.NewMessage(pattern='/link'))
async def link_handler(event):
    user_id = event.sender_id
    user_state[user_id] = "uploading"
    user_storage[user_id] = []
    await event.respond("✅ දැන් files එවන්න. ඉවර වුණාම 'Generate' ඔබන්න.")

@bot.on(events.NewMessage(incoming=True))
async def file_handler(event):
    user_id = event.sender_id
    # Command එකක් නෙවෙයි නම් සහ User 'uploading' state එකේ ඉන්නවා නම් පමණයි
    if not event.text.startswith('/') and user_state.get(user_id) == "uploading":
        user_storage[user_id].append(event.message.id)
        count = len(user_storage[user_id])
        buttons = [
            [Button.inline("තව තියෙනවා ➕", data="add_more")],
            [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]
        ]
        await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})", buttons=buttons)

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
        
        link = f"https://t.me/{(await bot.get_me()).username}?start={'x'.join(saved_ids)}"
        await event.edit(f"✅ **සාර්ථකයි!**\n\n`{link}`")
        user_storage[user_id] = []
        user_state[user_id] = None

# Clone feature එක දැනට අයින් කළා double message එක check කරන්න ලේසි වෙන්න
# මේක හරියට වැඩ කරනවා නම් මට කියන්න, මම clone එක ආපහු දාලා දෙන්නම්

async def main():
    await bot.start(bot_token=MAIN_BOT_TOKEN)
    print("රාජසිංහ වැඩ...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
