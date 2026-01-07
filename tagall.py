import random
import asyncio
import config
from core import app
from utils.decorators import ONLY_ADMIN, ONLY_GROUP
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

active_tasks = {}
task_messages = {}

POWERED = "<blockquote><b>Powered by : @Pranstore</b></blockquote>"

# =====================
# EMOJI RANDOM
# =====================
def random_emoji():
    emojis = "🍦 🎈 🎸 🌼 🌳 🚀 🎩 📷 💡 🏄‍♂️ 🎹 🚲 🍕 🌟 🎨 📚 🚁 🎮 🍔 🍉 🎉 🎵 🌸 🌈 🏝️ 🌞 🎢 🚗 🎭 🍩 🎲 📱 🏖️ 🛸 🧩 🚢 🎠 🏰 🎯 🥳 🎰 🛒 🧸 🛺 🧊 🛷 🦩 🎡 🎣 🏹 🧁 🥨 🎻 🎺 🥁 🛹".split()
    return random.choice(emojis)

# =====================
# PILIH DURASI
# =====================
def time_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏱ 3 Menit", callback_data="tagtime_180"),
                InlineKeyboardButton("⏱ 5 Menit", callback_data="tagtime_300"),
            ],
            [
                InlineKeyboardButton("⏱ 10 Menit", callback_data="tagtime_600"),
                InlineKeyboardButton("♾ Bebas", callback_data="tagtime_0"),
            ],
        ]
    )

# =====================
# START TAGALL
# =====================
@app.on_message(filters.command(["utag", "tagall", "all"]) & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def tagall_cmd(client, message):
    chat_id = message.chat.id

    if chat_id in active_tasks:
        return await message.reply("❌ TagAll sedang berjalan.")

    replied = message.reply_to_message
    text = None

    if len(message.command) > 1:
        text = message.text.split(maxsplit=1)[1]
    elif replied:
        text = replied.text or replied.caption

    if not text:
        return await message.reply("❗ Balas pesan atau isi teks TagAll.")

    starter = message.from_user

    active_tasks[chat_id] = {
        "text": text,
        "starter": starter.first_name,
        "starter_id": starter.id,
        "duration": "-",
    }

    task_messages[chat_id] = []

    await message.reply(
        "⏱ <b>Pilih durasi TagAll</b>",
        reply_markup=time_keyboard()
    )

# =====================
# CALLBACK DURASI
# =====================
@app.on_callback_query(filters.regex("^tagtime_"))
async def tagall_time_cb(client, cq):
    chat_id = cq.message.chat.id

    if chat_id not in active_tasks:
        return await cq.answer("TagAll tidak aktif", show_alert=True)

    try:
        await cq.message.delete()
    except:
        pass

    timeout = int(cq.data.split("_")[1])
    active_tasks[chat_id]["duration"] = (
        "3 menit" if timeout == 180 else
        "5 menit" if timeout == 300 else
        "10 menit" if timeout == 600 else
        "Bebas"
    )

    text = active_tasks[chat_id]["text"]

    async def tag_members():
        count = 0
        buffer = ""

        async for m in client.get_chat_members(chat_id):
            if chat_id not in active_tasks:
                break

            if m.user.is_bot or m.user.is_deleted:
                continue

            count += 1
            buffer += f"[{random_emoji()}](tg://user?id={m.user.id}) "

            if count == 10:
                msg = await client.send_message(
                    chat_id,
                    f"<b>{text}</b>\n{buffer}\n\n{POWERED}",
                    disable_web_page_preview=True
                )
                task_messages[chat_id].append(msg.id)
                buffer = ""
                count = 0
                await asyncio.sleep(4)

        if buffer:
            msg = await client.send_message(
                chat_id,
                f"<b>{text}</b>\n{buffer}\n\n{POWERED}",
                disable_web_page_preview=True
            )
            task_messages[chat_id].append(msg.id)

    try:
        if timeout > 0:
            await asyncio.wait_for(tag_members(), timeout)
        else:
            await tag_members()
    except asyncio.TimeoutError:
        pass
    finally:
        if chat_id in active_tasks:
            await notify_and_cleanup(client, chat_id)

# =====================
# COMMAND BATAL
# =====================
@app.on_message(filters.command(["batal", "cancel"]))
@ONLY_GROUP
@ONLY_ADMIN
async def cancel_tagall(client, message):
    chat_id = message.chat.id

    if chat_id not in active_tasks:
        return await message.reply("❌ Tidak ada TagAll yang berjalan.")

    data = active_tasks[chat_id]

    await message.reply(
        f"✅ <b>TagAll telah dibatalkan.</b>\n\n"
        f"👤 Dimulai oleh : {data['starter']}\n"
        f"⏱ Durasi yang dipilih : {data['duration']}\n\n"
        f"{POWERED}"
    )

    active_tasks.pop(chat_id, None)

# =====================
# CLEANUP + AUTO DELETE
# =====================
async def notify_and_cleanup(client, chat_id):
    notice = await client.send_message(
        chat_id,
        f"⏰ <b>Pesan TagAll akan dihapus</b>\n\n"
        f"Mohon tunggu 1 menit...\n\n"
        f"{POWERED}"
    )

    await asyncio.sleep(60)

    for msg_id in task_messages.get(chat_id, []):
        try:
            await client.delete_messages(chat_id, msg_id)
        except:
            pass

    try:
        await notice.delete()
    except:
        pass

    data = active_tasks.get(chat_id)
    if data:
        await client.send_message(
            chat_id,
            f"🧾 <b>TagAll selesai</b>\n\n"
            f"👤 Username : {data['starter']}\n"
            f"🆔 ID : <code>{data['starter_id']}</code>\n\n"
            f"{POWERED}"
        )

    active_tasks.pop(chat_id, None)
    task_messages.pop(chat_id, None)
