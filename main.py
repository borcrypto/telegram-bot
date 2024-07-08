import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import aiohttp
import instaloader
from tiktokpy import TikTokPy
import yt_dlp

# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hai! Pilih opsi untuk mengunduh video:\n\n'
                                    '1. /download_yt - Download video dari YouTube\n'
                                    '2. /download_tiktok - Download video dari TikTok\n'
                                    '3. /download_instagram - Download video dari Instagram\n'
                                    '4. /download_facebook - Download video dari Facebook')

async def download_yt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Pilih format untuk mengunduh video YouTube:\n\n'
                                    '/download_yt_mp3 - Download dalam format MP3\n'
                                    '/download_yt_mp4 - Download dalam format MP4')

async def download_yt_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await download_yt(update, context, 'mp3')

async def download_yt_mp4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await download_yt(update, context, 'mp4')

async def download_yt(update: Update, context: ContextTypes.DEFAULT_TYPE, format: str) -> None:
    try:
        url = context.args[0]
        await update.message.reply_text('Mengunduh video dari YouTube, harap tunggu...')
        
        loop = asyncio.get_event_loop()
        video_file = await loop.run_in_executor(None, download_video_from_yt, url, format)
        
        # Kirim video/audio menggunakan session HTTP dengan multipart/form-data
        async with aiohttp.ClientSession() as session:
            with open(video_file, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('chat_id', str(update.effective_chat.id))
                form.add_field('video' if format == 'mp4' else 'audio', f, filename=video_file, content_type='video/mp4' if format == 'mp4' else 'audio/mpeg')
                async with session.post(f'https://api.telegram.org/bot{API_TOKEN}/send{"Video" if format == "mp4" else "Audio"}', data=form) as response:
                    if response.status != 200:
                        await update.message.reply_text(f'Gagal mengirim video: {response.status}')
        
        os.remove(video_file)
    except Exception as e:
        await update.message.reply_text(f'Gagal mengunduh video: {e}')

def download_video_from_yt(url: str, format: str) -> str:
    if format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info_dict)
        if format == 'mp3':
            video_file = video_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
    return video_file

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = context.args[0]
        await update.message.reply_text('Mengunduh video dari TikTok, harap tunggu...')
        
        loop = asyncio.get_event_loop()
        video_file = await loop.run_in_executor(None, download_video_from_tiktok, url)
        
        # Kirim video menggunakan session HTTP dengan multipart/form-data
        async with aiohttp.ClientSession() as session:
            with open(video_file, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('chat_id', str(update.effective_chat.id))
                form.add_field('video', f, filename=video_file, content_type='video/mp4')
                async with session.post(f'https://api.telegram.org/bot{API_TOKEN}/sendVideo', data=form) as response:
                    if response.status != 200:
                        await update.message.reply_text(f'Gagal mengirim video: {response.status}')
        
        os.remove(video_file)
    except Exception as e:
        await update.message.reply_text(f'Gagal mengunduh video: {e}')

def download_video_from_tiktok(url: str) -> str:
    with TikTokPy() as tiktok:
        video = tiktok.get_video_no_watermark(url)
        video_file = f'{video.username}_{video.id}.mp4'
        tiktok.download_video(video, video_file)
    return video_file

async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = context.args[0]
        await update.message.reply_text('Mengunduh video dari Instagram, harap tunggu...')
        
        loop = asyncio.get_event_loop()
        video_file = await loop.run_in_executor(None, download_video_from_instagram, url)
        
        # Kirim video menggunakan session HTTP dengan multipart/form-data
        async with aiohttp.ClientSession() as session:
            with open(video_file, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('chat_id', str(update.effective_chat.id))
                form.add_field('video', f, filename=video_file, content_type='video/mp4')
                async with session.post(f'https://api.telegram.org/bot{API_TOKEN}/sendVideo', data=form) as response:
                    if response.status != 200:
                        await update.message.reply_text(f'Gagal mengirim video: {response.status}')
        
        os.remove(video_file)
    except Exception as e:
        await update.message.reply_text(f'Gagal mengunduh video: {e}')

def download_video_from_instagram(url: str) -> str:
    loader = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
    video_file = f'{post.owner_username}_{post.shortcode}.mp4'
    loader.download_post(post, target=video_file, filename="{post.profile}")
    return video_file

async def download_facebook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Maaf, fitur untuk mengunduh video dari Facebook belum diimplementasikan.')

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args[0].startswith('https://www.tiktok.com/'):
        await download_tiktok(update, context)
    elif context.args[0].startswith('https://www.instagram.com/'):
        await download_instagram(update, context)
    elif context.args[0].startswith('https://www.facebook.com/'):
        await download_facebook(update, context)
    else:
        await update.message.reply_text('URL tidak valid atau platform tidak didukung.')

def main() -> None:
    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('download_yt', download_yt_menu))
    application.add_handler(CommandHandler('download_yt_mp3', download_yt_mp3))
    application.add_handler(CommandHandler('download_yt_mp4', download_yt_mp4))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))

    application.run_polling()

if __name__ == '__main__':
    main()