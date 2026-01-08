import asyncio
import time
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core import app

# =====================
# STATE GLOBAL
# =====================
TAGALL_HOOK = {}
TAGALL_MSG_IDS = {}  # simpan semua message_id batch lama

# =====================
# INLINE KEYBOARD
# =====================
def tagall_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏱ 3 Menit", callback_data="hook_180"),
                InlineKeyboardButton("⏱ 5 Menit", callback_data="hook_300"),
            ],
            [
                InlineKeyboardButton("⏱ 10 Menit", callback_data="hook_600"),
                InlineKeyboardButton("♾ Bebas", callback_data="hook_free"),
            ],
            [
                InlineKeyboardButton("🚫 Stop", callback_data="hook_stop"),
            ],
        ]
    )

# =====================
# HOOK COMMAND LAMA
# =====================
@app.on_message(
    filters.command(["tagall", "utag", "all"]) & filters.group,
    group=-100
)
async def hook_tagall(_, message):
    chat_id = message.chat.id

    if TAGALL_HOOK.get(chat_id):
        message.stop_propagation()
        return

    TAGALL_HOOK[chat_id] = {
        "starter_id": message.from_user.id,
        "starter_mention": message.from_user.mention,
        "cmd_text": message.text,
        "start_time": None,
        "duration": None,
        "allow": False,
        "logged": False,
    }

    TAGALL_MSG_IDS[chat_id] = []

    await message.reply(
        "⏳ Pilih durasi TagAll:",
        reply_markup=tagall_keyboard()
    )

    message.stop_propagation()

# =====================
# TRACK MESSAGE TAGALL LAMA
# =====================
@app.on_message(filters.group, group=100)
async def track_old_tagall_messages(_, message):
    chat_id = message.chat.id
    if chat_id not in TAGALL_HOOK:
        return

    # deteksi pesan mention (heuristik aman)
    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" or ent.type == "mention":
                TAGALL_MSG_IDS[chat_id].append(message.id)
                break

# =====================
# CALLBACK
# =====================
@app.on_callback_query(filters.regex("^hook_"))
async def hook_callback(client, cq):
    chat_id = cq.message.chat.id
    user_id = cq.from_user.id
    meta = TAGALL_HOOK.get(chat_id)

    if not meta:
        return await cq.answer("TagAll sudah tidak aktif", show_alert=True)

    # =====================
    # STOP MANUAL
    # =====================
    if cq.data == "hook_stop":
        if user_id != meta["starter_id"]:
            try:
                member = await client.get_chat_member(chat_id, user_id)
                if member.status not in (
                    enums.ChatMemberStatus.ADMINISTRATOR,
                    enums.ChatMemberStatus.OWNER,
                ):
                    return await cq.answer(
                        "❌ Hanya admin atau pemulai TagAll yang bisa menghentikan.",
                        show_alert=True,
                    )
            except Exception:
                return await cq.answer("❌ Tidak punya izin.", show_alert=True)

        await stop_tagall(client, chat_id)
        await cq.answer("🚫 TagAll dihentikan", show_alert=True)
        return

    # =====================
    # SET DURASI
    # =====================
    duration = None if cq.data == "hook_free" else int(cq.data.split("_")[1])
    meta["duration"] = duration
    meta["start_time"] = time.time()
    meta["allow"] = True
    TAGALL_HOOK[chat_id] = meta

    await cq.message.delete()
    await cq.answer("✅ TagAll dimulai")

    # =====================
    # LOG SEKALI SAJA
    # =====================
    if not meta["logged"]:
        meta["logged"] = True
        await client.send_message(
            chat_id,
            f"📣 TagAll dimulai\n"
            f"👤 Oleh: {meta['starter_mention']}\n"
            f"⏱ Durasi: {'Bebas' if duration is None else str(duration // 60) + ' menit'}"
        )

    # =====================
    # JALANKAN COMMAND LAMA
    # =====================
    await client.send_message(chat_id, meta["cmd_text"])

    # =====================
    # AUTO STOP
    # =====================
    if duration:
        async def auto_stop():
            await asyncio.sleep(duration)
            await stop_tagall(client, chat_id, auto=True)

        asyncio.create_task(auto_stop())

# =====================
# STOP + AUTO DELETE
# =====================
async def stop_tagall(client, chat_id, auto=False):
    if chat_id not in TAGALL_HOOK:
        return

    try:
        await client.send_message(chat_id, "/cancel")
    except Exception:
        pass

    if auto:
        await client.send_message(
            chat_id,
            "🕒 TagAll selesai.\n🗑 Semua pesan TagAll akan dihapus dalam 1 menit."
        )
        await asyncio.sleep(60)

    # hapus semua batch message lama
    ids = TAGALL_MSG_IDS.get(chat_id, [])
    for mid in set(ids):
        try:
            await client.delete_messages(chat_id, mid)
        except Exception:
            pass

    TAGALL_HOOK.pop(chat_id, None)
    TAGALL_MSG_IDS.pop(chat_id, None)
