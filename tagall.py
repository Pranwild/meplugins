import random
import asyncio
import config
from core import app
from utils.decorators import ONLY_ADMIN, ONLY_GROUP
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

active_tasks = {}
task_messages = {}

POWERED = "\n\n<blockquote><b>Powered by @pranstore</b></blockquote>"

def random_emoji():
    emojis = "🍦 🎈 🎸 🌼 🌳 🚀 🎩 📷 💡 🏄‍♂️ 🎹 🚲 🍕 🌟 🎨 📚 🚁 🎮 🍔 🍉 🎉 🎵 🌸 🌈 🏝️ 🌞 🎢 🚗 🎭 🍩 🎲 📱 🏖️ 🛸 🧩 🚢 🎠 🏰 🎯 🥳 🎰 🛒 🧸 🛺 🧊 🛷 🦩 🎡 🎣 🏹 🧁 🥨 🎻 🎺 🥁 🛹".split()
    return random.choice(emojis)

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
            [
                InlineKeyboardButton("🛑 Batal Tagall", callback_data="tag_cancel")
            ],
        ]
    )

@app.on_message(filters.command(["utag", "all", "tagall"]) & ~config.BANNED_USERS)
@ONLY_GROUP
@ONLY_ADMIN
async def tagall_cmd(client, message):
    chat_id = message.chat.id

    if active_tasks.get(chat_id):
        return await message.reply("❌ Tagall sedang berjalan")

    replied = message.reply_to_message
    text = None

    if len(message.command) >= 2:
        text = message.text.split(maxsplit=1)[1]
    elif replied:
        text = replied.text or replied.caption

    if not text:
        return await message.reply("❗ Balas pesan atau isi teks tagall")

    starter = message.from_user
    starter_username = f"@{starter.username}" if starter.username else "-"
    starter_id = starter.id

    active_tasks[chat_id] = {
        "text": text,
        "end_log": (
            f"🧾 <b>Tagall berakhir</b>\n"
            f"• Username : {starter_username}\n"
            f"• ID : <code>{starter_id}</code>"
        )
    }

    task_messages[chat_id] = []

    await message.reply(
        "⏱ <b>Pilih durasi Tagall</b>",
        reply_markup=time_keyboard()
    )

@app.on_callback_query(filters.regex("^tagtime_"))
async def tagall_time_cb(client, cq: CallbackQuery):
    chat_id = cq.message.chat.id

    if chat_id not in active_tasks:
        return await cq.answer("❌ Tagall tidak aktif", show_alert=True)

    try:
        await cq.message.delete()
    except:
        pass

    timeout = int(cq.data.split("_")[1])
    text = active_tasks[chat_id]["text"]

    async def tag_members():
        usernum = 0
        usertxt = ""

        async for m in client.get_chat_members(chat_id):
            if chat_id not in active_tasks:
                break

            if m.user.is_deleted or m.user.is_bot:
                continue

            usernum += 1
            usertxt += f"[{random_emoji()}](tg://user?id={m.user.id}) "

            if usernum == 10:
                msg = await client.send_message(
                    chat_id,
                    f"<b>{text}</b>\n{usertxt}{POWERED}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🛑 Batal Tagall", callback_data="tag_cancel")]]
                    ),
                    disable_web_page_preview=True
                )
                task_messages[chat_id].append(msg.id)
                await asyncio.sleep(4)
                usernum = 0
                usertxt = ""

        if usertxt:
            msg = await client.send_message(
                chat_id,
                f"<b>{text}</b>\n{usertxt}{POWERED}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🛑 Batal Tagall", callback_data="tag_cancel")]]
                ),
                disable_web_page_preview=True
            )
            task_messages[chat_id].append(msg.id)

    try:
        if timeout > 0:
            await asyncio.wait_for(tag_members(), timeout=timeout)
        else:
            await tag_members()
    except asyncio.TimeoutError:
        pass
    finally:
        if chat_id in active_tasks:
            await notify_and_cleanup(client, chat_id)

@app.on_callback_query(filters.regex("^tag_cancel$"))
@ONLY_ADMIN
async def cancel_tagall_inline(client, cq: CallbackQuery):
    chat_id = cq.message.chat.id

    if chat_id not in active_tasks:
        return await cq.answer("❌ Tagall tidak aktif", show_alert=True)

    active_tasks.pop(chat_id, None)

    await cq.message.reply("🛑 <b>Tagall dibatalkan oleh admin</b>")
    await cq.answer("Tagall dibatalkan")

async def notify_and_cleanup(client, chat_id):
    notice = await client.send_message(
        chat_id,
        "⏳ <b>Tagall akan dihapus dalam 1 menit</b>"
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

    end_log = active_tasks[chat_id]["end_log"]
    await client.send_message(chat_id, end_log)

    active_tasks.pop(chat_id, None)
    task_messages.pop(chat_id, None)

