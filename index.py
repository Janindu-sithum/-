import asyncio
from telethon import TelegramClient, events, Button

# --- මූලික විස්තර ---
API_ID = 32917080
API_HASH = "31ad795e1bfd596494efb278f59488a3"
MAIN_BOT_TOKEN = "8302327984:AAHhvh71QMFNJqrnh58vsjRKwS5DvhZQp4M"
DB_CHANNEL_ID = -1003750069060

# දත්ත ගබඩා
user_storage = {}
user_state = {}
cloned_bots = [] # ක්‍රියාත්මක වන ක්ලෝන් බෝට්ස්ලා ලැයිස්තුව

async def setup_bot_handlers(client):
    """සියලුම බොට්ලා සඳහා පොදු ක්‍රියාකාරකම් මෙහි ඇත"""

    @client.on(events.NewMessage(pattern='/start'))
    async def start(event):
        # ලින්ක් එකක් හරහා පැමිණි විට
        if len(event.message.text.split()) > 1:
            msg_ids_raw = event.message.text.split()[1]
            msg_ids = [int(i) for i in msg_ids_raw.split('x')]
            await event.respond("🛡️ රාජසිංහ ඔබේ ගොනු ලබා ගනිමින් පවතියි...")
            for m_id in msg_ids:
                try:
                    await client.forward_messages(event.sender_id, m_id, DB_CHANNEL_ID)
                except:
                    continue
            return

        welcome = f"ආයුබෝවන් {event.sender.first_name}! මම රාජසිංහ. 👑\n\nලින්ක් එකක් හදන්න අවශ්‍ය නම් `/link` ලෙස type කරන්න."
        await event.respond(welcome)

    @client.on(events.NewMessage(pattern='/link'))
    async def link_cmd(event):
        user_id = event.sender_id
        user_state[user_id] = "uploading"
        user_storage[user_id] = []
        await event.respond("✅ දැන් ඔයාට share කරන්න ඕන files/messages මට එවන්න. ඒවා අවසන් වූ පසු 'Generate' බොත්තම ඔබන්න.")

    @client.on(events.NewMessage(pattern='/clone'))
    async def clone_bot(event):
        args = event.message.text.split()
        if len(args) < 2:
            return await event.respond("භාවිතය: `/clone BOT_TOKEN_HERE`")
        
        new_token = args[1]
        await event.respond("🔄 අලුත් Bot පණගන්වමින් පවතියි...")
        
        try:
            # නව බෝට් කෙනෙක් සෑදීම
            new_bot = TelegramClient(f"bot_{new_token[:8]}", API_ID, API_HASH)
            await new_bot.start(bot_token=new_token)
            await setup_bot_handlers(new_bot) # එම බොට්ටත් මේ handlers ම ලබා දීම
            cloned_bots.append(new_bot)
            await event.respond("✅ සාර්ථකයි! අලුත් Bot දැන් ක්‍රියාත්මකයි.")
        except Exception as e:
            await event.respond(f"❌ වැරදීමක්: {str(e)}")

    @client.on(events.NewMessage(incoming=True))
    async def handle_files(event):
        user_id = event.sender_id
        # මැසේජ් එකක් /link ලෙස ආරම්භ නොවන අතර user uploading state එකේ සිටිය යුතුයි
        if user_state.get(user_id) == "uploading" and not event.message.text.startswith('/'):
            if user_id not in user_storage:
                user_storage[user_id] = []
            
            user_storage[user_id].append(event.message.id)
            count = len(user_storage[user_id])
            
            buttons = [
                [Button.inline("තව තියෙනවා ➕", data="add_more")],
                [Button.inline("ලින්ක් එක හදන්න 🔗", data="gen_link")]
            ]
            await event.respond(f"✅ එකතු කරගත්තා! (ගොනු: {count})", buttons=buttons)

    @client.on(events.CallbackQuery)
    async def callback(event):
        user_id = event.sender_id
        if event.data == b"add_more":
            await event.answer("හරි, තව එවන්න!")
        elif event.data == b"gen_link":
            if user_id not in user_storage or not user_storage[user_id]:
                return await event.answer("කලින් file එකක් එවන්න!", alert=True)

            await event.edit("🔄 ලින්ක් එක සකසමින් පවතියි...")
            saved_ids = []
            for msg_id in user_storage[user_id]:
                # පණිවිඩය Database Channel එකට යැවීම
                sent_msg = await client.forward_messages(DB_CHANNEL_ID, msg_id, user_id)
                saved_ids.append(str(sent_msg.id))
            
            unique_string = "x".join(saved_ids)
            me = await client.get_me()
            share_link = f"https://t.me/{me.username}?start={unique_string}"
            
            await event.edit(f"✅ **සාර්ථකයි!**\n\nඔබේ ලින්ක් එක:\n`{share_link}`")
            # Reset user data
            user_storage[user_id] = []
            user_state[user_id] = None

# වැඩසටහන ආරම්භ කිරීම
async def main():
    main_bot = TelegramClient('rajasinghe_main', API_ID, API_HASH)
    await main_bot.start(bot_token=MAIN_BOT_TOKEN)
    
    # මෙතනදී handler එක register කරන්නේ එක්වරක් පමණයි
    await setup_bot_handlers(main_bot)
    
    print("රාජසිංහ Main Bot සාර්ථකව පණ ගැන්වුණා...")
    await main_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
