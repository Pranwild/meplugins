import asyncio
import random
import time
import config
from core import app
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from utils.decorators import ONLY_ADMIN, ONLY_GROUP

active_tagall = {}

EMOJIS = "🔥 ⚡ 🎯 🌸 💎 👑 🥶 🍀 🌈 🌟".split()

def rand_emoji():
    return random.choice(EMOJIS)

DURATIONS = {
    "1": 60,
    "3": 180,
    "5": 300,
    "60": 3600,
    "free": None
}


# ================= TAGALL COMMAND =================
@app.on_message(filters.command(["tagall", "utag", "all"]) & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def tagall_start(client, message):
    if message.chat.id in active_tagall:
        return await message.reply("<blockquote>❌ Tagall sedang berjalan</blockquote>")

    text = None
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    if not text:
        return await message.reply("<blockquote>❗ Reply pesan atau isi teks tagall</blockquote>")

    active_tagall[message.chat.id] = {
        "text": text,
        "starter": message.from_user
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏱ 1 Menit", callback_data="tagall_1"),
            InlineKeyboardButton("⏱ 3 Menit", callback_data="tagall_3"),
        ],
        [
            InlineKeyboardButton("⏱ 5 Menit", callback_data="tagall_5"),
            InlineKeyboardButton("⏱ 60 Menit", callback_data="tagall_60"),
        ],
        [
            InlineKeyboardButton("♾ Bebas", callback_data="tagall_free"),
        ],
        [
            InlineKeyboardButton("❌ Batal", callback_data="tagall_cancel"),
        ]
    ])

    await message.reply(
        "<blockquote>📣 <b>Pilih durasi Tagall</b></blockquote>",
        reply_markup=keyboard
    )


# ================= CALLBACK =================
@app.on_callback_query(filters.regex("^tagall_"))
async def tagall_callback(client, cq):
    chat_id = cq.message.chat.id

    if cq.data == "tagall_cancel":
        active_tagall.pop(chat_id, None)
        return await cq.message.edit("<blockquote>❌ Tagall dibatalkan</blockquote>")

    if chat_id not in active_tagall:
        return await cq.answer("Tagall sudah selesai", show_alert=True)

    key = cq.data.split("_")[1]
    duration = DURATIONS[key]
    data = active_tagall[chat_id]

    await cq.message.edit("<blockquote>🚀 <b>Tagall dimulai...</b></blockquote>")

    asyncio.create_task(
        run_tagall(
            client,
            chat_id,
            data["starter"],
            data["text"],
            duration
        )
    )


# ================= RUN TAGALL (NORMAL SPEED) =================
async def run_tagall(client, chat_id, starter, text, duration):
    start_time = time.time()
    mentioned = 0
    batch = []
    sent_msgs = []

    try:
        async for member in client.get_chat_members(chat_id):
            if chat_id not in active_tagall:
                break

            if duration and time.time() - start_time > duration:
                break

            user = member.user
            if user.is_bot or user.is_deleted:
                continue

            batch.append(
                f"<blockquote>[{rand_emoji()}](tg://user?id={user.id})</blockquote>"
            )
            mentioned += 1

            # NORMAL: 5 user per batch + delay
            if len(batch) == 5:
                msg = await client.send_message(
                    chat_id,
                    f"<b>{text}</b>\n\n"
                    + "".join(batch) +
                    "\n<blockquote><i>Powered by @pranstore</i></blockquote>",
                    disable_web_page_preview=True
                )
                sent_msgs.append(msg)
                batch.clear()
                await asyncio.sleep(2)  # ⬅️ delay normal

    except FloodWait as e:
        await asyncio.sleep(e.value)

    if batch:
        msg = await client.send_message(
            chat_id,
            f"<b>{text}</b>\n\n"
            + "".join(batch) +
            "\n<blockquote><i>Powered by @pranstore</i></blockquote>",
            disable_web_page_preview=True
        )
        sent_msgs.append(msg)

    # ================= NOTIFIKASI AUTO DELETE =================
    if duration:
        notify = await client.send_message(
            chat_id,
            "<blockquote>⏳ <b>Pesan Tagall akan dihapus dalam 1 menit</b></blockquote>"
        )

        await asyncio.sleep(60)

        try:
            await notify.delete()
        except:
            pass

        for m in sent_msgs:
            try:
                await m.delete()
            except:
                pass

    active_tagall.pop(chat_id, None)

    # ================= HASIL AKHIR =================
    await client.send_message(
        chat_id,
        f"<blockquote>"
        f"✅ <b>TAGALL SELESAI</b>\n\n"
        f"👤 Pemulai : {starter.mention}\n"
        f"📊 Total mention : <b>{mentioned} anggota</b>"
        f"</blockquote>"
    )


# ================= CANCEL =================
@app.on_message(filters.command("cancel") & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def cancel_tagall(_, message):
    if active_tagall.pop(message.chat.id, None):
        await message.reply("<blockquote>✅ Tagall dihentikan</blockquote>")
    else:
        await message.reply("<blockquote>⚠️ Tidak ada tagall aktif</blockquote>")
