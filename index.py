from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import uuid
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

app = Client(
    "rajasinha_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

db = sqlite3.connect("files.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS files(link_id TEXT,msg_id INTEGER,size INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS stats(downloads INTEGER)")
cursor.execute("INSERT OR IGNORE INTO stats VALUES (0)")
db.commit()

sessions = {}

def add_download():
    cursor.execute("UPDATE stats SET downloads = downloads + 1")
    db.commit()

def get_downloads():
    return cursor.execute("SELECT downloads FROM stats").fetchone()[0]

@app.on_message(filters.command("start"))
async def start(client, message):
    if len(message.command) > 1:
        link_id = message.command[1]
        rows = cursor.execute("SELECT msg_id FROM files WHERE link_id=?", (link_id,)).fetchall()
        if rows:
            for msg in rows:
                await client.copy_message(
                    message.chat.id,
                    CHANNEL_ID,
                    msg[0],
                    caption="📦 Shared via රාජසිංහ Bot"
                )
            add_download()
        else:
            await message.reply("❌ Link invalid")
        return

    await message.reply("👋 රාජසිංහ Bot වෙත සාදරයෙන් පිළිගනිමු!\n\n/link type කරලා share link එක හදන්න.")

@app.on_message(filters.command("link"))
async def link_mode(client, message):
    sessions[message.from_user.id] = []
    await message.reply("📤 files upload කරන්න.\nඅවසන් වූ විට /done type කරන්න.")

@app.on_message(filters.private & (filters.document | filters.photo | filters.video | filters.text))
async def save(client, message):
    uid = message.from_user.id
    if uid not in sessions:
        return

    size = 0
    if message.document:
        size = message.document.file_size
    elif message.video:
        size = message.video.file_size
    elif message.photo:
        size = message.photo[-1].file_size

    if message.text:
        sent = await client.send_message(CHANNEL_ID, message.text)
    else:
        sent = await message.copy(CHANNEL_ID)

    sessions[uid].append((sent.id, size))
    await message.reply("✔️ Added")

@app.on_message(filters.command("done"))
async def done(client, message):
    uid = message.from_user.id
    if uid not in sessions:
        return

    link_id = str(uuid.uuid4())[:8]
    total = 0
    for msg_id, size in sessions[uid]:
        cursor.execute("INSERT INTO files VALUES(?,?,?)", (link_id, msg_id, size))
        total += size
    db.commit()
    sessions[uid] = []

    link = f"https://t.me/{(await app.get_me()).username}?start={link_id}"
    await message.reply(f"🔗 Link:\n{link}\n📦 Size: {round(total/1024/1024,2)} MB")

@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin(client, message):
    files = cursor.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    downloads = get_downloads()
    storage = cursor.execute("SELECT SUM(size) FROM files").fetchone()[0] or 0
    await message.reply(
        f"👑 ADMIN PANEL\nFiles: {files}\nDownloads: {downloads}\nStorage: {round(storage/1024/1024,2)} MB"
    )

app.run()
