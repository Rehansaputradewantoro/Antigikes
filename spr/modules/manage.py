from os import remove

from pyrogram import filters
from pyrogram.types import Message

from spr import SUDOERS, arq, spr
from spr.utils.db import (disable_nsfw, disable_spam, enable_nsfw,
                          enable_spam, is_nsfw_enabled,
                          is_spam_enabled)
from spr.utils.misc import admins, get_file_id

__MODULE__ = "Manage"
__HELP__ = """
/anti_nsfw [ENABLE|DISABLE] - Enable or disable NSFW Detection.
/anti_spam, /Anti_Gikes [ENABLE|DISABLE, On|Off] - Enable or disable Spam Detection, Anti Gikes On or Off.

/nsfw_scan - Classify a media.
/spam_scan - Dapatkan prediksi Spam Gikes dari pesan balasan.
"""


@spr.on_message(
    filters.command("anti_nsfw") & ~filters.private, group=3
)
async def nsfw_toggle_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /anti_nsfw [ENABLE|DISABLE], [On|Off]"
        )
    if message.from_user:
        user = message.from_user
        chat_id = message.chat.id
        if user.id not in SUDOERS and user.id not in (
            await admins(chat_id)
        ):
            return await message.reply_text(
                "You don't have enough permissions"
            )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "enable":
        if is_nsfw_enabled(chat_id):
            return await message.reply("Already enabled, On.")
        enable_nsfw(chat_id)
        await message.reply_text("Enabled NSFW Detection, Terdeteksi NSFW On.")
    elif status == "disable":
        if not is_nsfw_enabled(chat_id):
            return await message.reply("Already disabled, Off.")
        disable_nsfw(chat_id)
        await message.reply_text("Disabled NSFW Detection. Terdeteksi NSFW Off")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /anti_nsfw [ENABLE|DISABLE]"
        )


@spr.on_message(
    filters.command("anti_spam, AntiGikes") & ~filters.private, group=3
)
async def spam_toggle_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /anti_spam [ENABLE|DISABLE], /Anti_Gikes [On|Off"
        )
    if message.from_user:
        user = message.from_user
        chat_id = message.chat.id
        if user.id not in SUDOERS and user.id not in (
            await admins(chat_id)
        ):
            return await message.reply_text(
                "Anda tidak memiliki cukup izin"
            )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "enable, On":
        if is_spam_enabled(chat_id):
            return await message.reply("Sudah diaktifkan, On.")
        enable_spam(chat_id)
        await message.reply_text("Deteksi Spam Gikes Diaktifkan.")
    elif status == "disable, Off":
        if not is_spam_enabled(chat_id):
            return await message.reply("Sudah Dimatikan, Off.")
        disable_spam(chat_id)
        await message.reply_text("Deteksi Spam Gikes Dinonaktifkan.")
    else:
        await message.reply_text(
            "Akhiran Tidak Diketahui, Gunakan /anti_spam or /Anti_Gikes [On|Off] [ENABLE|DISABLE]"
        )


@spr.on_message(filters.command("nsfw_scan"), group=3)
async def nsfw_scan_command(_, message: Message):
    err = "Membalas gambar/dokumen/stiker/animasi untuk memindainya."
    if not message.reply_to_message:
        await message.reply_text(err)
        return
    reply = message.reply_to_message
    if (
        not reply.document
        and not reply.photo
        and not reply.sticker
        and not reply.animation
        and not reply.video
    ):
        await message.reply_text(err)
        return
    m = await message.reply_text("Scanning")
    file_id = get_file_id(reply)
    if not file_id:
        return await m.edit("Ada yang salah.")
    file = await spr.download_media(file_id)
    try:
        results = await arq.nsfw_scan(file=file)
    except Exception as e:
        return await m.edit(str(e))
    remove(file)
    if not results.ok:
        return await m.edit(results.result)
    results = results.result
    await m.edit(
        f"""
**Neutral:** `{results.neutral} %`
**Porn:** `{results.porn} %`
**Hentai:** `{results.hentai} %`
**Sexy:** `{results.sexy} %`
**Drawings:** `{results.drawings} %`
**NSFW:** `{results.is_nsfw}`
"""
    )


@spr.on_message(filters.command("spam_scan"), group=3)
async def scanNLP(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("Balas pesan untuk memindainya.")
    r = message.reply_to_message
    text = r.text or r.caption
    if not text:
        return await message.reply("Can't scan that")
    data = await arq.nlp(text)
    data = data.result[0]
    msg = f"""
**Is Spam:** {data.is_spam}
**Spam Probability:** {data.spam_probability} %
**Spam:** {data.spam}
**Ham:** {data.ham}
**Profanity:** {data.profanity}
"""
    await message.reply(msg, quote=True)
