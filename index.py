import asyncio
import logging
from telethon import TelegramClient, events, Button

# --- Settings ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8302327984:AAFa4iJBJiYeQm1acQi1Z3uTHj4i_crlJ_c"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
processing_users = set() # Double message වැළැක්වීමට lock එකක්

def register_handlers(client):
    """සියලුම බෝට්ලාට (Main + Clones) අදාළ handlers මෙතැන ඇත"""

    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        if event.sender_id in processing_users: return
        
        # File retrieval logic
        if len(event.message.text.split()) > 1:
            msg_ids_raw = event.message.text.split()[1]
            msg_ids = [int(i) for i in msg_ids_raw.split('x')]
            await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
            for m_id in msg_ids:
                try: await client.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
                except: continue
            return

        await event.respond(f"ආයුබෝවන් {event.sender.first_name}! මම රාජසිංහ. 👑\n\nගොනු එවන්න කලින් `/link` ලෙස type කරන්න.")

    @client.on(events.NewMessage(pattern='/link'))
    async def link_cmd(event):
        user_id = event.sender_id
        user_state[user_id] = "uploading"
        user_storage[user_id] = []
        await event.respond("✅ දැන් මට ඕනෑම දෙයක් එවන්න. අවසන් වූ පසු 'Generate' ඔබන්න.")

    @client.on(events.NewMessage(pattern='/clone'))
    async def clone_cmd(event):
        args = event.message.text.split()
        if len(args) < 2:
            return await event.respond("භාවිතය: `/clone TOKEN`")
        
        token = args[1]
        await event.respond("🔄 අලුත් බොට් පණගන්වමින්...")
        try:
            # Clone session එකක් සෑදීම
            new_client = TelegramClient(f"session_{token[:8]}", API_ID, API_HASH)
            await new_client.start(bot_token=token)
            register_handlers(new_client)
            await event.respond("✅ Clone එක සාර්ථකයි!")
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")

    @client.on(events.NewMessage(incoming=True))
    async def handle_files(event):
        user_id = event.sender_id
        # Upload state එකේ සිටිය යුතු අතර command එකක් නොවිය යුතුය
        if user_state.get(user_id) == "uploading" and not event.text.startswith('/'):
            # Double message lock
            if user_id in processing_users: return
            processing_users.add(user_id)

            try:
                user_storage[user_id].append(event.message.id)
                count = len(user_storage[user_id])
                
                buttons = [
                    [Button.inline("තව තියෙනවා ➕", data="add_more")],
                    [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]
                ]
                await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})", buttons=buttons)
            finally:
                # තත්පරයකට පසු lock එක අයින් කරයි
                await asyncio.sleep(1)
                processing_users.discard(user_id)

    @client.on(events.CallbackQuery)
    async def callback(event):
        user_id = event.sender_id
        if event.data == b"add_more":
            await event.answer("හරි, තව එවන්න!")
        elif event.data == b"gen_link":
            if not user_storage.get(user_id):
                return await event.answer("කලින් file එකක් එවන්න!", alert=True)

            await event.edit("🔄 ලින්ක් එක සකසමින්...")
            saved_ids = []
            for m_id in user_storage[user_id]:
                msg = await client.forward_messages(DB_CHANNEL_ID, m_id, user_id)
                saved_ids.append(str(msg.id))
            
            me = await client.get_me()
            final_link = f"https://t.me/{me.username}?start={'x'.join(saved_ids)}"
            await event.edit(f"✅ **සාර්ථකයි!**\n\nඔබේ ලින්ක් එක:\n`{final_link}`")
            
            user_storage[user_id] = []
            user_state[user_id] = None

# --- Main Run ---
async def main():
    main_bot = TelegramClient('rajasinghe_main', API_ID, API_HASH)
    await main_bot.start(bot_token=MAIN_BOT_TOKEN)
    register_handlers(main_bot)
    print("රාජසිංහ සාර්ථකව පණගැන්වුණා!")
    await main_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
