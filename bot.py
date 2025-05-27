import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from yandex_music import Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# List of allowed user IDs from .env
ALLOWED_USERS = [int(id.strip()) for id in os.getenv('ALLOWED_USERS', '').split(',') if id.strip()]
ADMIN_ID = os.getenv('ADMIN_ID')

def is_user_allowed(user_id: int) -> bool:
    """Check if user is allowed to use the bot."""
    return len(ALLOWED_USERS) == 0 or user_id in ALLOWED_USERS

# Initialize Yandex Music client
yandex_client_with_token = Client(token=os.getenv('YANDEX_MUSIC_TOKEN')).init()
yandex_client_empty = Client().init()
#logger.info(os.getenv('TELEGRAM_BOT_TOKEN'))

async def send_admin_notification(application: Application, message: str):
    """Send notification to admin."""
    if not ADMIN_ID:
        return
    
    try:
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! Я бот для скачивания музыки из Яндекс.Музыки.\n'
        'Отправь мне название песни или ссылку на трек.'
    )
    
    # Отправляем уведомление администратору о новом пользователе
    if user.id != int(ADMIN_ID):
        await send_admin_notification(
            context.application,
            f"👤 Новый пользователь запустил бота:\n"
            f"ID: {user.id}\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username if user.username else 'Нет'}"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Я могу помочь вам скачать музыку из Яндекс.Музыки.\n\n'
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/help - Показать это сообщение\n'
        '/myid - Показать ваш Telegram ID\n\n'
        'Просто отправьте мне название песни или ссылку на трек в Яндекс.Музыке.\n\n'
        'Автор: @sboychenko_life'
    )

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send user's Telegram ID."""
    user = update.effective_user
    await update.message.reply_text(
        f'Ваш Telegram ID: `{user.id}`\n\n'
        'Этот ID можно использовать для идентификации в Telegram.',
        parse_mode='Markdown'
    )

async def search_tracks(clinet: Client, query: str, limit: int = 6):
    """Search for tracks in Yandex Music."""
    try:
        search_result = clinet.search(query, type_='track')
        if not search_result.tracks:
            return None
        
        tracks = []
        for track in search_result.tracks.results[:limit]:
            track_info = {
                'id': track.id,
                'title': track.title,
                'artists': ', '.join(artist.name for artist in track.artists),
                'duration': track.duration_ms // 1000,
                'album': track.albums[0].title if track.albums else 'Unknown Album'
            }
            tracks.append(track_info)
        return tracks
    except Exception as e:
        logger.error(f"Error searching tracks: {e}")
        return None

async def process_track(client: Client, track_id: str, message):
    """Process track download and sending."""
    try:
        # Get track info
        track = client.tracks(track_id)[0]
        artists = ', '.join(artist.name for artist in track.artists)
        album = track.albums[0].title if track.albums else 'Unknown Album'
        
        # Get download info
        download_info = track.get_download_info()
        if not download_info:
            await message.reply_text("❌ Трек недоступен для скачивания")
            return
        
        # Get the best available quality
        best_quality = None
        for info in download_info:
            if info.codec == 'mp3':
                if not best_quality or info.bitrate_in_kbps > best_quality.bitrate_in_kbps:
                    best_quality = info
        
        if not best_quality:
            await message.reply_text("❌ Не найдена подходящая версия трека")
            return
        
        # Download track
        filename = f"{track_id}.mp3"
        try:
            track.download(
                filename,
                codec=best_quality.codec,
                bitrate_in_kbps=best_quality.bitrate_in_kbps
            )
            
            # Send audio file with retries
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    with open(filename, 'rb') as audio:
                        await message.reply_audio(
                            audio=audio,
                            title=track.title,
                            performer=artists,
                            caption=f"🎵 {track.title}\n👤 {artists}",
                            read_timeout=30,
                            write_timeout=30,
                            connect_timeout=30,
                            pool_timeout=30
                        )
                    break  # If successful, break the retry loop
                except Exception as e:
                    if attempt < max_retries - 1:  # If not the last attempt
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise  # Re-raise the last exception if all attempts failed
            
            # Clean up
            os.remove(filename)
            
        except Exception as e:
            logger.error(f"Error during download/send: {e}")
            await message.reply_text("❌ Произошла ошибка при скачивании или отправке трека")
            if os.path.exists(filename):
                os.remove(filename)
                
    except Exception as e:
        logger.error(f"Error processing track: {e}")
        await message.reply_text("❌ Произошла ошибка при обработке трека")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text
    
    # Allow /myid command for all users
    if text == '/myid':
        await myid_command(update, context)
        return 
    
    # Check access for other commands and messages
    yandex_client = yandex_client_empty if not is_user_allowed(update.effective_user.id) else yandex_client_with_token
    
    if 'music.yandex' in text:
        # Handle Yandex Music URL
        await update.message.reply_text("🎵 Подготовка трека к скачиванию...")
        
        try:
            # Remove query parameters from URL
            text = text.split('?')[0]
            
            # Extract track ID from URL
            if '/track/' in text:
                track_id = text.split('/track/')[1].split('/')[0]
            elif '/album/' in text:
                track_id = text.split('/track/')[1].split('/')[0]
            else:
                await update.message.reply_text("❌ Неподдерживаемый формат ссылки")
                return

            await process_track(yandex_client, track_id, update.message)
                    
        except Exception as e:
            logger.error(f"Error processing URL: {e}")
            await update.message.reply_text("❌ Не удалось обработать ссылку")
            
    else:
        # Handle search query
        await update.message.reply_text(f"🔍 Ищу трек: {text}")
        
        tracks = await search_tracks(yandex_client, text)
        if not tracks:
            await update.message.reply_text(
                "😔 К сожалению, я не смог найти треки по вашему запросу. "
                "Попробуйте изменить поисковый запрос."
            )
            return
        
        # Create inline keyboard with search results
        keyboard = []
        for track in tracks:
            callback_data = f"track_{track['id']}"
            duration_min = track['duration'] // 60
            duration_sec = track['duration'] % 60
            button_text = f"{track['title']} - {track['artists']} ({duration_min}:{duration_sec:02d})"
            if len(button_text) > 64:
                button_text = button_text[:61] + "..."
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎵 Выберите трек для скачивания:",
            reply_markup=reply_markup
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboard."""
    query = update.callback_query
    await query.answer()

    # Check access for other commands and messages
    yandex_client = yandex_client_empty if not is_user_allowed(query.from_user.id) else yandex_client_with_token
    
    if not is_user_allowed(query.from_user.id):
        await query.message.reply_text(
            "🤖 Бот работает в демо режиме, треки в ознакомительном 30сек виде."
        )
    
    if query.data.startswith('track_'):
        track_id = query.data.split('_')[1]
        await query.message.reply_text("🎵 Подготовка трека к скачиванию...")
        await process_track(yandex_client, track_id, query.message)

async def main():
    """Start the bot."""
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Отправляем уведомление администратору о запуске бота
    await send_admin_notification(application, "🚀 Бот успешно запущен!")

    # Start the Bot
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            loop.close()
        except Exception as e:
            print(f"Error closing loop: {e}") 