import traceback
import time
from datetime import datetime, timedelta
from pyrogram import filters, enums, raw

from config import BANNED_USERS
from core import app
from utils import get_readable_time
from utils.database import dB, cleanmode, cleanmode_on, cleanmode_off
from utils.decorators import ONLY_ADMIN
from utils.functions import Tools
from utils.keyboard import Button
from strings import command
from utils.query_group import afk_group

__MODULE__ = "AFK"

__HELP__ = """
<blockquote expandable>

💤 <b>AFK Mode</b>

• <b>/afk [reason]</b> – Activate AFK status with optional reason.  
• You can also send a sticker, photo, or video to show your AFK.  
• To disable AFK, just send any message.

<i>Supports markdown & custom reply messages.</i>

</blockquote>
"""


afk_1 = ">**Unable to use the channel account.**"
afk_2 = ">**{a} is back online and has been AFK for** `{b}`\n"
afk_3 = ">**{a} is back online and has been AFK for** `{b}`\n**Reason:** `{c}`"
afk_4 = ">**{a} is back online**"
afk_5 = ">**Usage:**\n/{0} [ENABLE|DISABLE] to enable or disable automatic AFK message deletion."
afk_6 = ">**Automatic deletion of AFK messages in this chat is `enabled`**."
afk_7 = ">**Automatic deletion of AFK messages is `disabled`.**"
afk_8 = ">**{a} has been AFK since :** `{b}` **ago.**\n\n"
afk_9 = ">**{a} is currently AFK!.**"
afk_10 = ">**{a} has been AFK since :** `{b}` **ago.**\n\n**Reason:** `{c}`."
afk_11 = ">**{a} Now AFK!.**"

async def put_cleanmode(chat_id, message_id):
    if chat_id not in cleanmode:
        cleanmode[chat_id] = []
    time_now = datetime.now()
    put = {
        "msg_id": message_id,
        "timer_after": time_now + timedelta(minutes=1),
    }
    cleanmode[chat_id].append(put)


def get_media_path(user_id, afktype):
    ext = {"photo": "jpg", "video": "mp4"}.get(afktype)
    return f"downloads/{user_id}.{ext}" if ext else None

def online_afk_caption(afktype, user_mention, seenago, reasonafk):
    if afktype in ["text", "photo", "video", "animation"] and not reasonafk:
        return afk_2.format(a=user_mention, b=seenago)
    return afk_3.format(a=user_mention, b=seenago, c=reasonafk)


def still_afk_caption(afktype, user_mention, seenago, reasonafk):
    if afktype in ["text", "photo", "video", "animation"] and not reasonafk:
        return afk_8.format(a=user_mention, b=seenago)
    return afk_10.format(a=user_mention, b=seenago, c=reasonafk)


async def reply_afk_message(message, afktype, data, caption, user_id, reply_markup):
    if reply_markup is None:
        if afktype == "animation":
            return await message.reply_animation(data, caption=caption)
        elif afktype == "photo":
            return await message.reply_photo(photo=get_media_path(user_id, afktype), caption=caption)
        elif afktype == "video":
            return await message.reply_video(video=get_media_path(user_id, afktype), caption=caption)
        else:
            return await message.reply_text(caption, disable_web_page_preview=True)
    else:
        if afktype == "animation":
            return await message.reply_animation(data, caption=caption, reply_markup=reply_markup)
        elif afktype == "photo":
            return await message.reply_photo(photo=get_media_path(user_id, afktype), caption=caption, reply_markup=reply_markup)
        elif afktype == "video":
            return await message.reply_video(video=get_media_path(user_id, afktype), caption=caption, reply_markup=reply_markup)
        else:
            return await message.reply_text(caption, disable_web_page_preview=True, reply_markup=reply_markup)


async def handle_afk_reply(message, afktype, user_id, user_mention, timeafk, data, reasonafk, is_online: bool = False):
    seenago = get_readable_time(int(time.time() - timeafk))
    clean_text, buttons = Button.parse_msg_buttons(reasonafk)
    if buttons:
        reply_markup = await Button.create_inline_keyboard(buttons)
    else:
        reply_markup = None
    teks_formated = await Tools.escape_filter(message, clean_text, Tools.parse_words)
    if is_online:
        caption = online_afk_caption(afktype, user_mention, seenago, teks_formated)
    else:
        caption = still_afk_caption(afktype, user_mention, seenago, teks_formated)
    return await reply_afk_message(message, afktype, data, caption, user_id, reply_markup)

@app.on_message(filters.command(["afk", "brb"]) & ~BANNED_USERS)
async def active_afk(_, message):
    if message.sender_chat:
        return await message.reply_text(afk_1)

    user_id = message.from_user.id
    user_mention = message.from_user.mention
    user_firstname = message.from_user.first_name

    # Check if user already AFK
    afk_data = await dB.get_var(user_id, "AFK")
    if afk_data:
        try:
            send = await handle_afk_reply(
                message,
                afk_data["type"],
                user_id,
                user_mention,
                afk_data["time"],
                afk_data["data"],
                afk_data["reason"],
                is_online=True,
            )
        except Exception:
            send = await message.reply_text(afk_10.format(user_firstname, user_id))

        await put_cleanmode(message.chat.id, send.id)
        await dB.remove_var(user_id, "AFK")
        return

    # Setup new AFK
    reason = "Berak dulu"
    data = None
    afk_type = "text"

    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.animation:
            data = reply.animation.file_id
            afk_type = "animation"
            reason = reply.caption or ""
        elif reply.photo:
            await app.download_media(reply, file_name=f"{user_id}.jpg")
            afk_type = "photo"
            reason = reply.caption or ""
        elif reply.video:
            await app.download_media(reply, file_name=f"{user_id}.mp4")
            afk_type = "video"
            reason = reply.caption or ""
        elif reply.sticker:
            if reply.sticker.is_animated:
                afk_type = "text"
            else:
                await app.download_media(reply, file_name=f"{user_id}.mp4")
                afk_type = "video"
                reason = reply.caption or ""

    if afk_type == "text":
        if len(message.command) > 1:
            reason = message.text.split(None, 1)[1].strip()[:100]
            afk_type = "text"
    else:
        if len(message.command) > 1:
            reason = message.text.split(None, 1)[1].strip()[:100]


    details = {
        "type": afk_type,
        "time": time.time(),
        "data": data,
        "reason": reason,
    }
    await dB.set_var(user_id, "AFK", details)

    send = await message.reply_text(afk_11.format(a=user_mention, b=user_id))
    await put_cleanmode(message.chat.id, send.id)


    
@app.on_message(filters.command("afkdel") & filters.group)
@ONLY_ADMIN
async def afkdel_state(_, message):
    if not message.from_user:
        return
    if len(message.command) < 2:
        return await message.reply_text(afk_5.format(message.text.split()[0]))

    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await cleanmode_on(message.chat.id)
        await message.reply_text(afk_6)
    elif state == "disable":
        await cleanmode_off(message.chat.id)
        await message.reply_text(afk_7)
    else:
        await message.reply_text(afk_5.format(message.command[0]))

@app.on_message(filters.group & ~filters.bot & ~filters.via_bot, group=afk_group)
async def afk_watcher_func(client, message):
    if message.sender_chat:
        return

    msg = ""
    send = None
    user_id = message.from_user.id
    user_mention = message.from_user.mention

    if message.entities:
        possible = ["/afk", f"/afk@{client.me.username}", "!afk"]
        message_text = message.text or message.caption
        for entity in message.entities:
            if entity.type == enums.MessageEntityType.BOT_COMMAND:
                if message_text[:entity.length].lower() in possible:
                    return

    # AFK Checker untuk Pengirim Pesan
    afk_data = await dB.get_var(user_id, "AFK")
    if afk_data:
        try:
            send = await handle_afk_reply(
                message,
                afk_data["type"],
                user_id,
                user_mention,
                afk_data["time"],
                afk_data["data"],
                afk_data["reason"],
                is_online=True,
            )
        except Exception:
            print(traceback.format_exc())
        await dB.remove_var(user_id, "AFK")

    # AFK Checker untuk user yang di-reply
    if message.reply_to_message and message.reply_to_message.from_user:
        r_user = message.reply_to_message.from_user
        r_id = r_user.id
        r_mention = r_user.mention
        afk_data = await dB.get_var(r_id, "AFK")
        if afk_data:
            try:
                send = await handle_afk_reply(
                    message,
                    afk_data["type"],
                    r_id,
                    r_mention,
                    afk_data["time"],
                    afk_data["data"],
                    afk_data["reason"],
                    is_online=False
                )
            except Exception:
                print(traceback.format_exc())

    # AFK Checker via @mention dan text_mention
    if message.entities:
        for ent in message.entities:
            if ent.type in [enums.MessageEntityType.MENTION, enums.MessageEntityType.TEXT_MENTION]:
                try:
                    if ent.type == enums.MessageEntityType.MENTION:
                        username = message.text[ent.offset: ent.offset + ent.length].lstrip("@")
                        user = await client.get_users(username)
                    else:
                        user = ent.user
                    if user.id == message.from_user.id:
                        continue
                except Exception:
                    continue

                afk_data = await dB.get_var(user.id, "AFK")
                if afk_data:
                    try:
                        send = await handle_afk_reply(
                            message,
                            afk_data["type"],
                            user.id,
                            user.first_name[:25],
                            afk_data["time"],
                            afk_data["data"],
                            afk_data["reason"],
                            is_online=False
                        )
                    except Exception:
                        print(traceback.format_exc())

    if msg:
        try:
            send = await message.reply_text(msg, disable_web_page_preview=True)
        except Exception:
            pass

    if send:
        try:
            await put_cleanmode(message.chat.id, send.id)
        except Exception:
            pass


@app.on_raw_update()
async def on_reaction(client, update, users, chats):
    if not isinstance(update, raw.types.UpdateMessageReactions):
        return

    peer = update.peer
    msg_id = update.msg_id
    print(f"Peer: {peer}")
    print(f"Msg ID: {msg_id}")
    if isinstance(peer, raw.types.PeerChannel):
        chat_id = -100 + peer.channel_id
    elif isinstance(peer, raw.types.PeerChat):
        chat_id = -peer.chat_id
    elif isinstance(peer, raw.types.PeerUser):
        chat_id = peer.user_id
    else:
        return

    try:
        msg = await client.get_messages(chat_id, msg_id)
        if not msg or not msg.from_user:
            return

        afk_user_id = msg.from_user.id

        afk_data = await dB.get_var(afk_user_id, "AFK")
        if not afk_data:
            return

        reactors = update.reactions.recent_reactions
        for react in reactors:
            reactor_id = react.peer_id.user_id
            if reactor_id == afk_user_id:
                continue  

            afk_text = await handle_afk_reply(
                msg,
                afk_data["type"],
                afk_user_id,
                msg.from_user.mention,
                afk_data["time"],
                afk_data["data"],
                afk_data["reason"],
                is_online=False,
            )

            await client.send_message(chat_id, afk_text, reply_to_message_id=msg_id)

    except Exception:
        print(traceback.format_exc())
