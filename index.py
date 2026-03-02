import asyncio
from telethon import TelegramClient, events, Button, errors

# --- මූලික විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
# අලුත්ම Token එක මෙතනට දාන්න
MAIN_BOT_TOKEN = "8601021475:AAE3miHZ6ttekbHffkfx7SMb_Mbw3xnC0SY"
DB_CHANNEL_ID = -1003750069060

user_storage = {}
user_state = {}

def register_handlers(client):
    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        if len(event.message.text.split()) > 1:
            msg_ids = [int(i) for i in event.message.text.split()[1].split('x')]
            await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
            for m_id in msg_ids:
                try: await client.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
                except: continue
            return
        await event.respond(f"ආයුබෝවන්! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න `/link` එවන්න.")

    @client.on(events.NewMessage(pattern='/link'))
    async def link_cmd(event):
        user_id = event.sender_id
        user_state[user_id] = "uploading"
        user_storage[user_id] = []
        await event.respond("✅ දැන් මට ඕනෑම දෙයක් එවන්න. අවසන් වූ පසු 'Generate' ඔබන්න.")

    @client.on(events.NewMessage(pattern='/clone'))
    async def clone_cmd(event):
        args = event.message.text.split()
        if len(args) < 2: return await event.respond("භාවිතය: `/clone TOKEN`")
        
        token = args[1]
        await event.respond("🔄 අලුත් බොට් පණගන්වමින්...")
        try:
            # Token එක වලංගු ද කියා පරීක්ෂා කරමින් පණගැන්වීම
            new_client = TelegramClient(f"session_{token[:8]}", API_ID, API_HASH)
            await new_client.start(bot_token=token)
            register_handlers(new_client)
            await event.respond("✅ Clone එක සාර්ථකයි!")
        except errors.rpcerrorlist.AccessTokenExpiredError:
            await event.respond("❌ ඔය Token එක දැන් වැඩ කරන්නේ නැහැ (Expired). අලුත් එකක් අරන් එවන්න.")
        except Exception as e:
            await event.respond(f"❌ වැරදීමක්: {str(e)}")

    @client.on(events.NewMessage(incoming=True))
    async def handle_files(event):
        user_id = event.sender_id
        if user_state.get(user_id) == "uploading" and not event.text.startswith('/'):
            user_storage[user_id].append(event.message.id)
            count = len(user_storage[user_id])
            buttons = [[Button.inline("තව තියෙනවා ➕", data="add_more")],
                       [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]]
            await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})", buttons=buttons)

    @client.on(events.CallbackQuery)
    async def callback(event):
        user_id = event.sender_id
        if event.data == b"gen_link":
            if not user_storage.get(user_id): return await event.answer("කලින් file එකක් එවන්න!", alert=True)
            await event.edit("🔄 ලින්ක් එක සකසමින්...")
            saved_ids = [str((await client.forward_messages(DB_CHANNEL_ID, m, user_id)).id) for m in user_storage[user_id]]
            me = await client.get_me()
            final_link = f"https://t.me/{me.username}?start={'x'.join(saved_ids)}"
            await event.edit(f"✅ **සාර්ථකයි!**\n\n`{final_link}`")
            user_storage[user_id] = []; user_state[user_id] = None

async def main():
    try:
        main_bot = TelegramClient('rajasinghe_main', API_ID, API_HASH)
        await main_bot.start(bot_token=MAIN_BOT_TOKEN)
        register_handlers(main_bot)
        print("රාජසිංහ වැඩ...")
        await main_bot.run_until_disconnected()
    except errors.rpcerrorlist.AccessTokenExpiredError:
        print("CRITICAL: Main Bot Token එක Expire වෙලා! අලුත් එකක් දාන්න.")

if __name__ == '__main__':
    asyncio.run(main())
