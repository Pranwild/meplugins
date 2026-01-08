import asyncio
import random
import time
import config
from core import app
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from utils.decorators import ONLY_ADMIN, ONLY_GROUP

active_tagall = {}

EMOJIS = "🍦 🎈 🎸 🌼 🌳 🚀 🎩 📷 💡 🏄‍♂️ 🎹 🚲 🍕 🌟 🎨 📚 🚁 🎮 🍔 🍉 🎉 🎵 🌸 🌈 🏝️ 🌞 🎢 🚗 🎭 🍩 🎲 📱 🏖️ 🛸 🧩 🚢 🎠 🏰 🎯 🥳".split()

def rand_emoji():
    return random.choice(EMOJIS)

DURATIONS = {
    "1": 60,
    "3": 180,
    "5": 300,
    "60": 3600,
    "free": None
}


@app.on_message(filters.command(["tagall", "utag", "all"]) & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def tagall_start(client, message):
    if message.chat.id in active_tagall:
        return await message.reply("❌ Tagall sedang berjalan, gunakan /cancel")

    text = None
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    if not text:
        return await message.reply("❗ Reply pesan atau isi teks tagall")

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏱ 1 Menit", callback_data="tagall_1"),
            InlineKeyboardButton("⏱ 3 Menit", callback_data="tagall_3")
        ],
        [
            InlineKeyboardButton("⏱ 5 Menit", callback_data="tagall_5"),
            InlineKeyboardButton("⏱ 60 Menit", callback_data="tagall_60")
        ],
        [
            InlineKeyboardButton("♾ Bebas", callback_data="tagall_free")
        ],
        [
            InlineKeyboardButton("❌ Batal", callback_data="tagall_cancel")
        ]
    ])

    active_tagall[message.chat.id] = {
        "text": text,
        "starter": message.from_user
    }

    await message.reply("📣 **Pilih durasi Tagall**", reply_markup=kb)


@app.on_callback_query(filters.regex("^tagall_"))
async def tagall_callback(client, cq):
    chat_id = cq.message.chat.id

    if cq.data == "tagall_cancel":
        active_tagall.pop(chat_id, None)
        return await cq.message.edit("❌ Tagall dibatalkan")

    if chat_id not in active_tagall:
        return await cq.answer("Tagall sudah tidak aktif", show_alert=True)

    key = cq.data.split("_")[1]
    duration = DURATIONS[key]
    data = active_tagall[chat_id]

    await cq.message.edit("🚀 Tagall dimulai...")

    asyncio.create_task(
        run_tagall(
            client,
            chat_id,
            cq.from_user,
            data["text"],
            duration
        )
    )


async def run_tagall(client, chat_id, starter, text, duration):
    start_time = time.time()
    mentioned = 0
    batch = []
    sent_messages = []

    active_tagall[chat_id]["running"] = True

    try:
        async for member in client.get_chat_members(chat_id):
            if chat_id not in active_tagall:
                break

            if duration and time.time() - start_time > duration:
                break

            user = member.user
            if user.is_bot or user.is_deleted:
                continue

            batch.append(f"[{rand_emoji()}](tg://user?id={user.id})")
            mentioned += 1

            if len(batch) == 7:
                msg = await client.send_message(
                    chat_id,
                    f"**{text}**\n\n" +
                    " ".join(batch) +
                    "\n\n`power by : @pranstore`",
                    disable_web_page_preview=True
                )
                sent_messages.append(msg)
                batch.clear()
                await asyncio.sleep(3)

        if batch:
            msg = await client.send_message(
                chat_id,
                f"**{text}**\n\n" +
                " ".join(batch) +
                "\n\n`power by : @pranstore`",
                disable_web_page_preview=True
            )
            sent_messages.append(msg)

    except FloodWait as e:
        await asyncio.sleep(e.value)

    # tunggu 1 menit sebelum hapus
    if duration:
        await asyncio.sleep(60)
        for m in sent_messages:
            try:
                await m.delete()
            except:
                pass

    active_tagall.pop(chat_id, None)

    await client.send_message(
        chat_id,
        f"✅ **TAGALL SELESAI**\n\n"
        f"👤 Pemulai : {starter.mention}\n"
        f"📊 Total mention : **{mentioned} anggota**"
    )


@app.on_message(filters.command("cancel") & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def cancel_tagall(client, message):
    if active_tagall.pop(message.chat.id, None):
        await message.reply("✅ Tagall dihentikan")
    else:
        await message.reply("⚠️ Tidak ada tagall aktif")
