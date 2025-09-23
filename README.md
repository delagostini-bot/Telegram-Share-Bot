# 🤖 Telegram Media Backup Bot

A comprehensive Telegram bot system that automatically forwards and organizes media content from multiple groups/channels to a centralized backup supergroup. The bot creates organized topics for each source and provides a web-based dashboard for monitoring and configuration.

## ✨ Features

### 🔄 **Automatic Media Forwarding**
- Monitors multiple Telegram groups and channels
- Forwards all media types (photos, videos, documents, audio, voice notes, stickers, animations)
- Removes "forwarded from" attribution for cleaner organization
- Adds source identification to each forwarded media

### 📁 **Smart Topic Organization**
- Automatically creates topics in the backup supergroup for each source
- Groups media by source channel/group name
- Advanced duplicate detection prevents duplicate topics
- Unicode normalization handles emojis and special characters

### 📊 **Web Dashboard**
- Real-time monitoring and statistics
- Bot control (start/stop/restart)
- Configuration management
- Activity logs and analytics
- System performance monitoring

### ⚙️ **Easy Configuration**
- One-click setup with `start.py`
- Automatic dependency installation
- Persistent configuration storage
- User-friendly web interface for settings

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- A Telegram account
- Basic computer knowledge

### 1. **Easy Installation (Recommended)**

Simply run the `start.py` file and everything will be configured automatically:

```bash
python start.py
```

**That's it!** The script will:
- ✅ Check and install all required dependencies
- ✅ Guide you through bot token configuration
- ✅ Help you set up the backup group
- ✅ Start the bot automatically
- ✅ Open the web dashboard

### 2. **Manual Installation (Advanced Users)**

If you prefer manual setup:

```bash
# Install dependencies
pip install pyTelegramBotAPI python-dotenv streamlit plotly pandas psutil

# Set environment variables
export BOT_TOKEN="your_bot_token_here"
export BACKUP_GROUP_ID="your_group_id_here"

# Run the bot
python bot/telegram_bot.py

# In another terminal, run the dashboard
streamlit run app.py --server.port 5000
```

## 🔧 Detailed Setup Guide

### Step 1: Create Your Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a conversation** with BotFather by sending `/start`
3. **Create a new bot** by sending `/newbot`
4. **Choose a name** for your bot (e.g., "My Media Backup Bot")
5. **Choose a username** for your bot (must end with 'bot', e.g., "my_media_backup_bot")
6. **Copy the bot token** - it looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
7. **Save this token** - you'll need it during setup

### Step 2: Create Your Backup Supergroup

1. **Create a new group** in Telegram
2. **Add at least one other member** (you can remove them later)
3. **Convert to supergroup**: 
   - Go to group settings
   - Tap "Group Type"
   - Select "Public Group" then change back to "Private Group"
4. **Enable Topics**:
   - Go to group settings
   - Tap "Topics"
   - Enable "Topics"
5. **Add your bot** to the group:
   - Add the bot using its username (e.g., @my_media_backup_bot)
   - Make the bot an **Administrator**
   - Give it **"Manage Topics"** permission

### Step 3: Get Your Group ID

**Method 1: Using @userinfobot (Recommended)**
1. **Add @userinfobot** to your backup supergroup
2. **The bot will automatically send** the group ID (looks like `-1001234567890`)
3. **Copy this ID** - you'll need it during setup
4. **Remove @userinfobot** from the group

**Method 2: Using Bot API**
1. **Add your bot** to the group first
2. **Send a message** in the group
3. **Visit**: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. **Look for** the chat object with "type": "supergroup"
5. **Copy the negative ID** from the "id" field

### Step 4: Run the Setup

Execute the `start.py` script:

```bash
python start.py
```

The script will ask for:
- **Bot Token**: Paste the token from BotFather
- **Group ID**: Paste the negative ID from your supergroup

## 📱 Dashboard Features

The web dashboard is accessible at `http://localhost:5000` and provides:

### 🏠 **Overview Tab**
- Total messages processed
- Active topics count
- Today's activity
- Source groups statistics

### 📈 **Analytics Tab**
- Daily activity charts (last 7 days)
- Hourly activity patterns (last 24 hours)
- Media type distribution
- Source group performance

### 📋 **Topics Tab**
- List of all created topics
- Thread IDs and media counts
- Topic management interface

### 📄 **Logs Tab**
- Real-time activity feed
- Recent media forwards
- Success/failure status
- Source and media type details

### ⚙️ **Configuration Sidebar**
- Bot token management
- Backup group ID settings
- Bot control (start/stop/restart)
- System status monitoring

## 🔧 Configuration Options

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
BOT_TOKEN=your_bot_token_here
BACKUP_GROUP_ID=your_group_id_here
```

### Ignored Chats

To ignore specific groups/channels, edit `bot/telegram_bot.py`:

```python
# Add chat IDs to ignore
IGNORED_CHAT_IDS = [-1001234567890, -1009876543210]
```

### File Structure

```
📁 Your Project/
├── 📄 start.py              # Easy setup script
├── 📄 app.py                # Streamlit dashboard
├── 📄 config.json           # Bot configuration
├── 📁 bot/
│   ├── 📄 telegram_bot.py   # Main bot script
│   ├── 📄 topics.json       # Topic mappings
│   ├── 📄 stats.json        # Statistics data
│   └── 📄 activity_logs.json # Activity logs
└── 📁 utils/
    ├── 📄 analytics.py      # Analytics engine
    ├── 📄 bot_monitor.py    # Bot monitoring
    ├── 📄 config_manager.py # Configuration management
    └── 📄 duplicate_detector.py # Duplicate detection
```

## 🎯 How It Works

### Media Detection
The bot monitors all groups and channels it's added to and automatically detects:
- 📸 Photos
- 🎥 Videos  
- 📄 Documents
- 🎵 Audio files
- 🎤 Voice messages
- 🎬 Video notes
- 🎭 Stickers
- 🎞️ Animations/GIFs

### Topic Creation
When media is detected from a new source:
1. **Normalizes** the group/channel name (removes emojis, special characters)
2. **Checks for duplicates** using advanced similarity detection
3. **Creates a new topic** in the backup supergroup if no duplicate found
4. **Saves the mapping** between source name and topic thread ID

### Media Processing
For each media item:
1. **Downloads** the original media
2. **Re-uploads** to remove "forwarded from" label
3. **Adds source caption** indicating the original group/channel
4. **Posts to appropriate topic** in the backup supergroup
5. **Logs the activity** for dashboard analytics

## 🛠️ Troubleshooting

### Common Issues

**❌ "BOT_TOKEN not set" Error**
- Make sure you ran `start.py` and entered a valid bot token
- Check that the token was saved correctly in `config.json`
- Verify the token format: should be numbers:letters (e.g., `123456789:ABCdef...`)

**❌ "Group ID not found" Error**
- Ensure the group ID is negative (supergroups always have negative IDs)
- Verify your bot is an administrator in the backup group
- Check that "Topics" are enabled in the group settings

**❌ "Permission denied" Error**
- Make sure your bot has "Manage Topics" permission
- Verify your bot is an administrator, not just a member
- Try removing and re-adding the bot with proper permissions

**❌ Bot not responding to media**
- Check that the bot is running (`python start.py`)
- Verify the source groups aren't in the IGNORED_CHAT_IDS list
- Ensure the bot has permission to read messages in source groups

**❌ Dashboard not loading**
- Make sure port 5000 is not being used by another application
- Try accessing `http://localhost:8000` for the basic monitor
- Check console logs for error messages

### Advanced Troubleshooting

**Check Bot Status**
```bash
# In Telegram, send to your bot:
/start
/status
```

**Check Logs**
```bash
# View real-time logs while bot runs:
python bot/telegram_bot.py
```

**Test Configuration**
```bash
# Verify your configuration:
python -c "import json; print(json.load(open('config.json')))"
```

**Reset Configuration**
```bash
# Delete config and start fresh:
rm config.json
python start.py
```

## 📖 Additional Features

### Statistics Tracking
- **Real-time metrics** on media processing
- **Historical data** with charts and graphs
- **Source performance** analytics
- **Media type breakdown**

### Duplicate Detection
- **Unicode normalization** for international characters
- **Fuzzy matching** for similar group names
- **Configurable similarity threshold**
- **Manual override capabilities**

### Process Monitoring
- **Automatic bot restart** on crashes
- **Memory and CPU monitoring**
- **Uptime tracking**
- **Health checks**

## 🤝 Support

### Getting Help
1. **Check this README** for common solutions
2. **Review the troubleshooting section** above
3. **Check the dashboard logs** for specific error messages
4. **Verify your configuration** using the dashboard

### Configuration Best Practices
- **Regular backups** of your `config.json` and `bot/topics.json` files
- **Monitor disk space** if processing large media files
- **Keep bot token secure** - never share it publicly
- **Use strong permissions** on your backup supergroup

## 📋 Requirements

### System Requirements
- **Python 3.11+** (recommended)
- **2GB RAM minimum** (more for heavy usage)
- **Stable internet connection**
- **Available ports 5000 and 8000**

### Python Dependencies
The `start.py` script automatically installs:
- `pyTelegramBotAPI` - Telegram Bot API wrapper
- `python-dotenv` - Environment variable management
- `streamlit` - Web dashboard framework
- `plotly` - Interactive charts and graphs
- `pandas` - Data manipulation and analysis
- `psutil` - System monitoring

## 🔒 Security Notes

- **Keep your bot token secret** - never commit it to version control
- **Use environment variables** or the secure config system
- **Regularly update dependencies** for security patches
- **Monitor bot permissions** in all connected groups
- **Review activity logs** for unusual behavior

## 🎉 You're All Set!

Once everything is configured:

1. **The bot runs automatically** and monitors all connected groups
2. **Media is forwarded** and organized by topic
3. **Dashboard shows real-time stats** at `http://localhost:5000`
4. **Configuration can be changed** through the web interface
5. **Everything is logged** for monitoring and troubleshooting

**Enjoy your organized media backup system!** 🚀

---

*Need help? Check the troubleshooting section above or review the configuration in your web dashboard.*