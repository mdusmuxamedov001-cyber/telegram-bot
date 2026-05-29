"""
Professional Telegram Media Downloader Bot
Supports: YouTube, Instagram, TikTok, Twitter/X, SoundCloud
Languages: English, Russian, Uzbek
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import yt_dlp

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BOT_TOKEN = "8256146248:AAH6s5tNjKlbQ_zZj3uoLIFW8Dzif3d3GGk"
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE_MB = 50

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── TRANSLATIONS ──────────────────────────────────────────────────────────────

TEXTS = {
    "welcome": {
        "en": (
            "🎉 *Welcome to Media Downloader Bot!*\n\n"
            "Send me a link from:\n"
            "▶️ YouTube\n📸 Instagram\n🎵 TikTok\n🐦 Twitter / X\n🎶 SoundCloud\n\n"
            "I will download it as MP3 or MP4!\n\n"
            "🌐 Change language: /lang\n📖 Help: /help"
        ),
        "ru": (
            "🎉 *Добро пожаловать в Media Downloader Bot!*\n\n"
            "Отправьте ссылку с:\n"
            "▶️ YouTube\n📸 Instagram\n🎵 TikTok\n🐦 Twitter / X\n🎶 SoundCloud\n\n"
            "Скачаю как MP3 или MP4!\n\n"
            "🌐 Язык: /lang\n📖 Помощь: /help"
        ),
        "uz": (
            "🎉 *Media Downloader Botga xush kelibsiz!*\n\n"
            "Quyidagi saytlardan havola yuboring:\n"
            "▶️ YouTube\n📸 Instagram\n🎵 TikTok\n🐦 Twitter / X\n🎶 SoundCloud\n\n"
            "MP3 yoki MP4 formatda yuklab beraman!\n\n"
            "🌐 Til: /lang\n📖 Yordam: /help"
        ),
    },
    "choose_lang": {
        "en": "🌐 Choose your language:",
        "ru": "🌐 Выберите язык:",
        "uz": "🌐 Tilni tanlang:",
    },
    "lang_set": {
        "en": "✅ Language set to *English*!",
        "ru": "✅ Язык установлен: *Русский*!",
        "uz": "✅ Til o'rnatildi: *O'zbek*!",
    },
    "no_link": {
        "en": "❌ No supported link found.\n\nPlease send a YouTube, Instagram, TikTok, Twitter or SoundCloud link.",
        "ru": "❌ Ссылка не найдена.\n\nОтправьте ссылку с YouTube, Instagram, TikTok, Twitter или SoundCloud.",
        "uz": "❌ Havola topilmadi.\n\nYouTube, Instagram, TikTok, Twitter yoki SoundCloud havolasini yuboring.",
    },
    "link_found": {
        "en": "🔗 *Link detected!*\n\nChoose format:",
        "ru": "🔗 *Ссылка найдена!*\n\nВыберите формат:",
        "uz": "🔗 *Havola topildi!*\n\nFormat tanlang:",
    },
    "choose_quality": {
        "en": "🎬 Choose video quality:",
        "ru": "🎬 Выберите качество видео:",
        "uz": "🎬 Video sifatini tanlang:",
    },
    "downloading": {
        "en": "⏳ Downloading... please wait.",
        "ru": "⏳ Загрузка... пожалуйста, подождите.",
        "uz": "⏳ Yuklanmoqda... iltimos kuting.",
    },
    "sending": {
        "en": "✅ Done! Sending your file...",
        "ru": "✅ Готово! Отправляю файл...",
        "uz": "✅ Tayyor! Fayl yuborilmoqda...",
    },
    "too_large": {
        "en": "⚠️ File too large for Telegram (50MB limit).\nTry lower quality or MP3.",
        "ru": "⚠️ Файл слишком большой (лимит 50МБ).\nПопробуйте меньшее качество или MP3.",
        "uz": "⚠️ Fayl juda katta (50MB limit).\nPast sifat yoki MP3 ni sinab ko'ring.",
    },
    "error": {
        "en": "❌ Download failed.\n\nReasons:\n• Private/age-restricted content\n• Geo-blocked\n• Invalid link\n\nTry another link.",
        "ru": "❌ Ошибка загрузки.\n\nПричины:\n• Приватный контент\n• Гео-блокировка\n• Неверная ссылка\n\nПопробуйте другую ссылку.",
        "uz": "❌ Yuklab bo'lmadi.\n\nSabablari:\n• Shaxsiy kontent\n• Geo-bloklangan\n• Noto'g'ri havola\n\nBoshqa havola sinab ko'ring.",
    },
    "help": {
        "en": (
            "📖 *How to use:*\n\n"
            "1️⃣ Send a video/music link\n"
            "2️⃣ Choose *MP3* or *MP4*\n"
            "3️⃣ For MP4, choose quality\n"
            "4️⃣ Receive your file!\n\n"
            "✅ Supported sites:\nYouTube, Instagram, TikTok, Twitter, SoundCloud\n\n"
            "⚠️ Max file size: 50MB\n"
            "🌐 Change language: /lang"
        ),
        "ru": (
            "📖 *Как пользоваться:*\n\n"
            "1️⃣ Отправьте ссылку\n"
            "2️⃣ Выберите *MP3* или *MP4*\n"
            "3️⃣ Для MP4 выберите качество\n"
            "4️⃣ Получите файл!\n\n"
            "✅ Поддерживаемые сайты:\nYouTube, Instagram, TikTok, Twitter, SoundCloud\n\n"
            "⚠️ Макс. размер: 50МБ\n"
            "🌐 Язык: /lang"
        ),
        "uz": (
            "📖 *Qanday ishlatish:*\n\n"
            "1️⃣ Havola yuboring\n"
            "2️⃣ *MP3* yoki *MP4* tanlang\n"
            "3️⃣ MP4 uchun sifat tanlang\n"
            "4️⃣ Faylingizni oling!\n\n"
            "✅ Qo'llab-quvvatlanadigan saytlar:\nYouTube, Instagram, TikTok, Twitter, SoundCloud\n\n"
            "⚠️ Maks hajm: 50MB\n"
            "🌐 Til: /lang"
        ),
    },
}

def t(key: str, lang: str) -> str:
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", ""))

def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")

# ─── URL DETECTION ─────────────────────────────────────────────────────────────

SUPPORTED_PATTERNS = [
    r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+",
    r"https?://(www\.)?instagram\.com/\S+",
    r"https?://(www\.)?tiktok\.com/\S+",
    r"https?://(www\.)?(twitter\.com|x\.com)/\S+",
    r"https?://(www\.)?soundcloud\.com/\S+",
    r"https?://(www\.)?music\.youtube\.com/\S+",
]

def extract_url(text: str) -> str | None:
    for pattern in SUPPORTED_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

# ─── DOWNLOAD ──────────────────────────────────────────────────────────────────

def build_ydl_opts(fmt: str, quality: str, output_path: Path) -> dict:
    outtmpl = str(output_path / "%(title).60s.%(ext)s")
    common = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "socket_timeout": 30,
    }
    if fmt == "mp3":
        return {
            **common,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    quality_format = {
        "360": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    }
    return {
        **common,
        "format": quality_format.get(quality, quality_format["720"]),
        "merge_output_format": "mp4",
    }


async def download_media(url: str, fmt: str, quality: str) -> tuple[Path | None, str]:
    opts = build_ydl_opts(fmt, quality, DOWNLOAD_DIR)
    loop = asyncio.get_event_loop()

    def _do_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base = Path(filename).stem
            for ext in ["mp3", "mp4", "mkv", "webm", "m4a"]:
                candidate = DOWNLOAD_DIR / f"{base}.{ext}"
                if candidate.exists():
                    return candidate
            p = Path(filename)
            return p if p.exists() else None

    try:
        file_path = await asyncio.wait_for(
            loop.run_in_executor(None, _do_download),
            timeout=300
        )
        if file_path and file_path.exists():
            return file_path, ""
        return None, "File not found after download."
    except asyncio.TimeoutError:
        return None, "Download timed out."
    except yt_dlp.utils.DownloadError as e:
        return None, str(e)[:300]
    except Exception as e:
        return None, str(e)[:300]

# ─── HANDLERS ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("welcome", lang), parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("help", lang), parse_mode="Markdown")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    keyboard = [[
        InlineKeyboardButton("🇬🇧 English", callback_data="setlang:en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang:ru"),
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="setlang:uz"),
    ]]
    await update.message.reply_text(
        t("choose_lang", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(t("lang_set", lang), parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    url = extract_url(update.message.text)
    if not url:
        await update.message.reply_text(t("no_link", lang))
        return
    context.user_data["url"] = url
    keyboard = [[
        InlineKeyboardButton("🎵 MP3", callback_data="fmt:mp3"),
        InlineKeyboardButton("🎬 MP4", callback_data="fmt:mp4"),
    ]]
    await update.message.reply_text(
        t("link_found", lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_fmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    fmt = query.data.split(":")[1]
    context.user_data["fmt"] = fmt
    if fmt == "mp3":
        context.user_data["quality"] = "best"
        await query.edit_message_text(t("downloading", lang))
        await do_download(query, context)
    else:
        keyboard = [[
            InlineKeyboardButton("📱 360p", callback_data="quality:360"),
            InlineKeyboardButton("💻 720p HD", callback_data="quality:720"),
            InlineKeyboardButton("🖥 1080p FHD", callback_data="quality:1080"),
        ]]
        await query.edit_message_text(
            t("choose_quality", lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    quality = query.data.split(":")[1]
    context.user_data["quality"] = quality
    await query.edit_message_text(t("downloading", lang))
    await do_download(query, context)

async def do_download(query, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    url = context.user_data.get("url")
    fmt = context.user_data.get("fmt", "mp4")
    quality = context.user_data.get("quality", "720")

    if not url:
        await query.message.reply_text(t("no_link", lang))
        return

    file_path, error = await download_media(url, fmt, quality)

    if error or not file_path:
        logger.error(f"Download error: {error}")
        await query.message.reply_text(t("error", lang))
        return

    size_mb = file_path.stat().st_size / (1024 * 1024)

    try:
        if size_mb > MAX_FILE_SIZE_MB:
            await query.message.reply_text(t("too_large", lang))
        else:
            await query.message.reply_text(t("sending", lang))
            with open(file_path, "rb") as f:
                if fmt == "mp3":
                    await query.message.reply_audio(
                        audio=f,
                        filename=file_path.name,
                        read_timeout=60,
                        write_timeout=60
                    )
                else:
                    await query.message.reply_video(
                        video=f,
                        filename=file_path.name,
                        supports_streaming=True,
                        read_timeout=60,
                        write_timeout=60
                    )
    except Exception as e:
        logger.error(f"Send error: {e}")
        await query.message.reply_text(t("error", lang))
    finally:
        try:
            file_path.unlink()
        except Exception:
            pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update error:", exc_info=context.error)

# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CallbackQueryHandler(handle_setlang, pattern=r"^setlang:"))
    app.add_handler(CallbackQueryHandler(handle_fmt, pattern=r"^fmt:"))
    app.add_handler(CallbackQueryHandler(handle_quality, pattern=r"^quality:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 Bot is running!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1,
    )

if __name__ == "__main__":
    main()
