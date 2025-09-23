#!/usr/bin/env python3
"""
Telegram Bot to forward media from groups/channels to a backup supergroup
Organizes media into topics by source group/channel
"""

import json
import logging
import os
import time
import re
import unicodedata
from typing import Dict, Optional
from datetime import datetime  # 👈 ADICIONADO

import telebot
from telebot.types import Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot settings
BOT_TOKEN = os.getenv('BOT_TOKEN')
BACKUP_GROUP_ID_STR = os.getenv('BACKUP_GROUP_ID')

# 🚫 IDs of chats/channels to be ignored
IGNORED_CHAT_IDS = [-100000000000]

# Validate and convert BACKUP_GROUP_ID
if not BACKUP_GROUP_ID_STR:
    raise ValueError("BACKUP_GROUP_ID not set! Use start.py to configure.")

try:
    BACKUP_GROUP_ID = int(BACKUP_GROUP_ID_STR)
except ValueError:
    raise ValueError(f"Invalid BACKUP_GROUP_ID: {BACKUP_GROUP_ID_STR}")

# File to store topic mappings
TOPICS_FILE = 'bot/topics.json'

def normalize_topic_name(name: str) -> str:
    """Normalize topic name to better detect duplicates"""
    if not name:
        return ""
    
    # Remove accents and normalize unicode
    normalized = unicodedata.normalize('NFD', name)
    no_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    # Remove emojis and special characters, keep only letters, numbers and spaces
    ascii_only = ''.join(char if ord(char) < 128 else ' ' for char in no_accents)
    
    # Remove punctuation and normalize spaces
    clean = re.sub(r'[^\w\s]', ' ', ascii_only)
    clean = re.sub(r'\s+', ' ', clean).strip().lower()
    
    return clean

# 📊 Função para registrar estatísticas — NOVA
def log_forwarded_media(source_topic: str, media_type: str, message_id: int, status: str = "success"):
    """Registra no log e atualiza estatísticas do dashboard"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source_topic,
            "media_type": media_type,
            "message_id": message_id,
            "status": status
        }

        logs_file = 'bot/activity_logs.json'
        stats_file = 'bot/stats.json'

        # --- Atualiza activity_logs.json ---
        logs = []
        if os.path.exists(logs_file):
            with open(logs_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
                except json.JSONDecodeError:
                    logs = []

        logs.append(log_entry)
        logs = logs[-1000:]  # Mantém apenas os últimos 1000 registros

        os.makedirs('bot', exist_ok=True)
        with open(logs_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        # --- Atualiza stats.json ---
        stats = {
            "total_messages": 0,
            "today_messages": 0,
            "week_messages": 0,
            "topics": {}
        }

        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                try:
                    stats = json.load(f)
                    if not isinstance(stats, dict):
                        stats = {}
                except json.JSONDecodeError:
                    pass

        # Garante que a estrutura básica existe
        stats.setdefault("total_messages", 0)
        stats.setdefault("today_messages", 0)
        stats.setdefault("week_messages", 0)
        stats.setdefault("topics", {})

        # Incrementa contadores
        stats["total_messages"] += 1
        stats["today_messages"] += 1
        stats["week_messages"] += 1

        # Incrementa contador por tópico
        if source_topic not in stats["topics"]:
            stats["topics"][source_topic] = 0
        stats["topics"][source_topic] += 1

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Estatísticas atualizadas para: {source_topic} ({media_type})")

    except Exception as e:
        logger.error(f"❌ Falha ao registrar estatísticas: {e}")


class TelegramBackupBot:
    def __init__(self):
        """Initialize Telegram bot"""
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN not set! Define it as an environment variable.")
        
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.topics: Dict[str, int] = self.load_topics()
        self.setup_handlers()
        
    def load_topics(self) -> Dict[str, int]:
        """Load topic mapping from JSON file"""
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Migrate old format (chat_id -> group_name) if necessary
                if data and list(data.keys())[0].startswith('-'):
                    logger.info("Migrating old topics.json format...")
                    return {}  # Start empty to recreate with names
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_topics(self):
        """Save topic mapping to JSON file"""
        try:
            os.makedirs(os.path.dirname(TOPICS_FILE), exist_ok=True)
            with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.topics, f, ensure_ascii=False, indent=2)
            logger.debug(f"Topics saved: {len(self.topics)} records")
        except Exception as e:
            logger.error(f"Error saving topics: {e}")
    
    def get_or_create_topic(self, chat_id: int, source_name: str) -> Optional[int]:
        """
        Get existing topic ID or create a new real topic
        Uses GROUP NAME as key to avoid duplicates
        
        Args:
            chat_id: Source chat ID
            source_name: Source group/channel name
            
        Returns:
            Real topic ID or None if error
        """
        normalized_name = normalize_topic_name(source_name)
        
        for existing_name, thread_id in self.topics.items():
            existing_normalized = normalize_topic_name(existing_name)
            if existing_normalized == normalized_name:
                logger.info(f"Similar topic found: '{existing_name}' for '{source_name}' (Thread ID: {thread_id})")
                return thread_id
        
        try:
            logger.info(f"Creating new topic for group: {source_name}")
            topic = self.bot.create_forum_topic(
                chat_id=BACKUP_GROUP_ID,
                name=source_name[:128]  # Max 128 chars
            )
            
            thread_id = None
            if hasattr(topic, 'message_thread_id'):
                thread_id = topic.message_thread_id
            elif hasattr(topic, 'thread_id'):
                thread_id = topic.thread_id  
            elif hasattr(topic, 'id'):
                thread_id = topic.id
            else:
                logger.warning(f"create_forum_topic returned object without identifiable thread ID: {topic}")
                return None
            
            self.topics[source_name] = thread_id
            self.save_topics()
            
            logger.info(f"✅ New topic created: '{source_name}' (Thread ID: {thread_id})")
            return thread_id
            
        except Exception as e:
            logger.error(f"❌ Error creating topic for '{source_name}': {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            return None
    
    def has_media(self, message: Message) -> bool:
        """Check if message contains media"""
        return bool(message.photo or message.video or message.document or 
                    message.audio or message.voice or message.video_note or 
                    message.sticker or message.animation)
    
    def forward_media(self, message: Message) -> bool:
        """
        Process media to backup supergroup.
        If forwarded, downloads and resends to remove "forwarded from".
        Always adds caption with source: "— Source: Group Name"
        
        Args:
            message: Message with media
            
        Returns:
            True if successful
        """
        source_name = "Unknown"
        try:
            source_chat = message.chat
            source_name = source_chat.title or source_chat.first_name or f"Chat_{source_chat.id}"
            
            topic_id = self.get_or_create_topic(source_chat.id, source_name)
            if topic_id is None:
                logger.error(f"Could not get/create topic for {source_name}")
                return False

            original_caption = message.caption or ""
            new_caption = f"{original_caption}\n\n— Source: {source_name}".strip()

            is_forwarded = bool(message.forward_from or message.forward_from_chat)

            if not is_forwarded:
                try:
                    logger.info(f"Copying original media from {source_name} with new caption...")
                    self.bot.copy_message(
                        chat_id=BACKUP_GROUP_ID,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id,
                        message_thread_id=topic_id,
                        caption=new_caption
                    )
                    logger.info(f"✅ Media copied successfully from {source_name}")

                    # 📊 Registrar estatísticas — ADICIONADO
                    log_forwarded_media(
                        source_topic=source_name,
                        media_type="photo" if message.photo else
                                   "video" if message.video else
                                   "document" if message.document else
                                   "audio" if message.audio else
                                   "voice" if message.voice else
                                   "video_note" if message.video_note else
                                   "sticker" if message.sticker else
                                   "animation" if message.animation else
                                   "unknown",
                        message_id=message.message_id
                    )

                    return True
                except Exception as copy_error:
                    logger.warning(f"copy_message failed (probably media without original caption): {copy_error}")
            else:
                logger.info(f"Forwarded message detected from {source_name}. Downloading and resending...")

            # 🚨 Fallback: manual resend
            if message.photo:
                file_id = message.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_photo(
                    chat_id=BACKUP_GROUP_ID,
                    photo=downloaded_file,
                    caption=new_caption,
                    message_thread_id=topic_id
                )

            elif message.video:
                file_id = message.video.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_video(
                    chat_id=BACKUP_GROUP_ID,
                    video=downloaded_file,
                    caption=new_caption,
                    message_thread_id=topic_id
                )

            elif message.document:
                file_id = message.document.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_document(
                    chat_id=BACKUP_GROUP_ID,
                    document=downloaded_file,
                    caption=new_caption,
                    message_thread_id=topic_id
                )

            elif message.audio:
                file_id = message.audio.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_audio(
                    chat_id=BACKUP_GROUP_ID,
                    audio=downloaded_file,
                    caption=new_caption,
                    message_thread_id=topic_id
                )

            elif message.voice:
                file_id = message.voice.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_voice(
                    chat_id=BACKUP_GROUP_ID,
                    voice=downloaded_file,
                    caption=new_caption if new_caption.strip() else None,
                    message_thread_id=topic_id
                )

            elif message.video_note:
                file_id = message.video_note.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_video_note(
                    chat_id=BACKUP_GROUP_ID,
                    video_note=downloaded_file,
                    message_thread_id=topic_id
                )
                if new_caption.strip():
                    self.bot.send_message(
                        chat_id=BACKUP_GROUP_ID,
                        text=new_caption,
                        message_thread_id=topic_id
                    )

            elif message.animation:
                file_id = message.animation.file_id
                file_info = self.bot.get_file(file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                self.bot.send_animation(
                    chat_id=BACKUP_GROUP_ID,
                    animation=downloaded_file,
                    caption=new_caption,
                    message_thread_id=topic_id
                )

            elif message.sticker:
                self.bot.send_sticker(
                    chat_id=BACKUP_GROUP_ID,
                    sticker=message.sticker.file_id,
                    message_thread_id=topic_id
                )
                if new_caption.strip():
                    self.bot.send_message(
                        chat_id=BACKUP_GROUP_ID,
                        text=new_caption,
                        message_thread_id=topic_id
                    )

            else:
                logger.warning("Unsupported media type for manual resend.")
                return False

            logger.info(f"✅ Media resent manually from {source_name} (without forward, with source caption)")

            # 📊 Registrar estatísticas — ADICIONADO
            log_forwarded_media(
                source_topic=source_name,
                media_type="photo" if message.photo else
                           "video" if message.video else
                           "document" if message.document else
                           "audio" if message.audio else
                           "voice" if message.voice else
                           "video_note" if message.video_note else
                           "sticker" if message.sticker else
                           "animation" if message.animation else
                           "unknown",
                message_id=message.message_id
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error processing media from {source_name}: {e}")

            # 📊 Registrar falha — ADICIONADO
            try:
                log_forwarded_media(
                    source_topic=source_name,
                    media_type="unknown",
                    message_id=getattr(message, 'message_id', 0),
                    status="failed"
                )
            except Exception:
                pass  # Não deixar falha de log quebrar o bot

            return False
    
    def setup_handlers(self):
        """Configure bot handlers"""
        
        def process_media(message: Message):
            """Process media from group message or channel post"""
            try:
                if message.from_user and message.from_user.is_bot:
                    return
                if message.chat.type not in ['group', 'supergroup', 'channel']:
                    return
                if message.chat.id in IGNORED_CHAT_IDS:
                    logger.info(f"Ignoring media from chat {message.chat.id} (in ignored list)")
                    return
                if message.chat.id == BACKUP_GROUP_ID:
                    return
                if not self.has_media(message):
                    return
                
                logger.info(f"Media detected in chat {message.chat.title or message.chat.id} (ID: {message.chat.id})")
                success = self.forward_media(message)
                
                if success:
                    logger.info("Media processed successfully")
                else:
                    logger.warning("Failed to process media")
                    
            except Exception as e:
                logger.error(f"Error processing media: {e}")
        
        @self.bot.message_handler(content_types=[
            'photo', 'video', 'document', 'audio', 
            'voice', 'video_note', 'sticker', 'animation'
        ])
        def handle_media(message: Message):
            """Handler for group/supergroup media"""
            process_media(message)
        
        @self.bot.channel_post_handler(content_types=[
            'photo', 'video', 'document', 'audio', 
            'voice', 'video_note', 'sticker', 'animation'
        ])
        def handle_channel_media(message: Message):
            """Handler for channel posts"""
            process_media(message)
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message: Message):
            """Handler for /start command"""
            if message.chat.type != 'private':
                return
                
            self.bot.reply_to(message,
                "🤖 **Telegram Backup Bot**\n\n"
                "This bot automatically processes media from groups and channels "
                "to the backup supergroup, organizing them into topics.\n\n"
                "📁 **Features:**\n"
                "• Detects media (photos, videos, documents)\n"
                "• Resends as new messages — without 'forwarded from...'\n"
                "• Adds source caption\n"
                "• Organizes by topics\n"
                "• Ignores configured channels\n\n"
                "✅ **Status:** Active and monitoring media",
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(commands=['status'])
        def status_command(message: Message):
            """Handler for /status command"""
            if message.chat.type != 'private':
                return
                
            topics_count = len(self.topics)
            if self.topics:
                topics_list = "\n".join([
                    f"• {name} (Thread ID: {thread_id})" 
                    for name, thread_id in list(self.topics.items())[:10]
                ])
            else:
                topics_list = "No topics created yet."
            
            self.bot.reply_to(message,
                f"📊 **Bot Status**\n\n"
                f"🎯 **Backup supergroup:** `{BACKUP_GROUP_ID}`\n"
                f"📁 **Mapped topics:** {topics_count}\n"
                f"✅ **Status:** Operational\n\n"
                f"📝 **Existing topics:**\n{topics_list}",
                parse_mode='Markdown'
            )
    
    def start_polling(self):
        """Start bot in polling mode"""
        try:
            logger.info("Starting Telegram backup bot...")
            me = self.bot.get_me()
            logger.info(f"Bot logged in as: @{me.username}")
            logger.info("Bot started successfully! Press Ctrl+C to stop.")
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")

def main():
    """Main function to start the bot"""
    try:
        if not BOT_TOKEN:
            print("❌ ERROR: BOT_TOKEN not set!")
            print("Set the BOT_TOKEN environment variable with your bot token.")
            return
        bot = TelegramBackupBot()
        bot.start_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    main()