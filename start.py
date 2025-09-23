#!/usr/bin/env python3
"""
🤖 TELEGRAM BOT INITIALIZER
============================

This script makes it easy for non-technical users to use the bot.
Double-click this file to start everything automatically!

Features:
• Starts the Telegram bot automatically
• Opens web interface to monitor statistics
• Shows clear configuration instructions
• User-friendly interface for non-technical users
• Saves configurations permanently after first execution
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
import json
from datetime import datetime

# List of required dependencies
REQUIRED_PACKAGES = [
    'pyTelegramBotAPI',
    'python-dotenv', 
    'flask',
    'flask-socketio',
    'psutil'
]

# Configuration file
CONFIG_FILE = 'config.json'

def print_header():
    """Shows program header"""
    print("=" * 60)
    print("🤖 TELEGRAM BOT - AUTOMATIC INITIALIZER")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%d/%m/%Y at %H:%M:%S')}")
    print()

def print_step(step_num, description):
    """Shows current step"""
    print(f"📋 Step {step_num}: {description}")
    print("-" * 50)

def load_config():
    """Loads configuration from JSON file"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "bot_token": "",
            "backup_group_id": "",
            "created_at": "",
            "last_updated": ""
        }

def save_config(config):
    """Saves configuration to JSON file"""
    config["last_updated"] = datetime.now().isoformat()
    if not config.get("created_at"):
        config["created_at"] = config["last_updated"]
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def check_dependencies():
    """Checks and installs required dependencies"""
    print("🔍 Checking dependencies...")
    
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace('-', '_').lower())
        except ImportError:
            # Try alternative names
            alt_names = {
                'pyTelegramBotAPI': 'telebot',
                'python-dotenv': 'dotenv',
                'flask-socketio': 'flask_socketio'
            }
            alt_name = alt_names.get(package)
            if alt_name:
                try:
                    __import__(alt_name)
                    continue
                except ImportError:
                    pass
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing dependencies: {', '.join(missing_packages)}")
        print("")
        print("📦 Installing automatically...")
        
        try:
            for package in missing_packages:
                print(f"   → Installing {package}...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"   ❌ Error installing {package}")
                    print(f"   💡 Run manually: pip install {package}")
                    return False
                else:
                    print(f"   ✅ {package} installed!")
            
            print("✅ All dependencies installed!")
            return True
            
        except Exception as e:
            print(f"❌ Error in automatic installation: {e}")
            print("")
            print("📝 INSTALL MANUALLY:")
            for package in missing_packages:
                print(f"   pip install {package}")
            return False
    else:
        print("✅ All dependencies found!")
        return True

def get_token_input():
    """Requests bot token from user"""
    print("❌ Bot token not configured!")
    print()
    print("📝 CONFIGURATION INSTRUCTIONS:")
    print("1. Open Telegram and search for '@BotFather'")
    print("2. Send /start to BotFather")
    print("3. Send /newbot and follow the instructions")
    print("4. Copy the token provided by BotFather")
    print()
    print("🔑 Paste your bot token here:")
    return input("Token: ").strip()

def get_group_id_input():
    """Requests group ID from user"""
    print("❌ Backup supergroup ID not configured!")
    print("")
    print("📝 HOW TO GET THE SUPERGROUP ID:")
    print("1. Create a supergroup on Telegram")
    print("2. Enable 'Topics' in the group settings")
    print("3. Add @userinfobot to the group")
    print("4. The bot will show the group ID (negative number)")
    print("5. Remove @userinfobot afterwards")
    print("")
    print("💡 Example ID: -1001234567890")
    print("")
    print("🔢 Paste your supergroup ID here:")
    return input("Supergroup ID: ").strip()

def setup_initial_config():
    """Initial configuration - requests token and group ID"""
    config = load_config()
    
    # Check if configuration is already saved
    if config.get("bot_token") and config.get("backup_group_id"):
        print("✅ Configuration found!")
        print(f"   🔑 Token: {config['bot_token'][:10]}...")
        print(f"   🏢 Group: {config['backup_group_id']}")
        print(f"   📅 Configured on: {config.get('created_at', 'N/A')}")
        
        # Set environment variables for this session
        os.environ['BOT_TOKEN'] = config['bot_token']
        os.environ['BACKUP_GROUP_ID'] = config['backup_group_id']
        return True
    
    print("🔧 First execution detected - initial configuration required")
    print()
    
    # Request token
    while not config.get("bot_token"):
        user_token = get_token_input()
        if user_token:
            config["bot_token"] = user_token
            break
        else:
            print("❌ Token not provided. Try again...")
    
    # Request group ID
    while not config.get("backup_group_id"):
        user_id = get_group_id_input()
        if user_id:
            try:
                # Remove spaces and check if it's a number
                clean_id = user_id.replace(' ', '').replace(',', '')
                int(clean_id)
                
                if not clean_id.startswith('-'):
                    print("⚠️ Warning: Supergroup IDs usually start with '-'")
                    confirm = input("Are you sure it's correct? (y/N): ").lower()
                    if confirm != 'y':
                        continue
                
                config["backup_group_id"] = clean_id
                break
                
            except ValueError:
                print("❌ Invalid ID. Must be a number. Try again...")
        else:
            print("❌ ID not provided. Try again...")
    
    # Save configuration
    if save_config(config):
        print("✅ Configuration saved permanently!")
        print("💡 Next time, no reconfiguration will be needed")
        
        # Set environment variables for this session
        os.environ['BOT_TOKEN'] = config['bot_token']
        os.environ['BACKUP_GROUP_ID'] = config['backup_group_id']
        return True
    else:
        print("❌ Error saving configuration.")
        return False

def start_telegram_bot():
    """Starts the Telegram bot in a separate process"""
    print("🚀 Starting Telegram bot...")
    
    try:
        # Prepare environment variables
        env = os.environ.copy()
        
        # Start bot as separate process WITHOUT capturing stdout/stderr to avoid deadlock
        process = subprocess.Popen(
            [sys.executable, 'bot/telegram_bot.py'],
            env=env
        )
        
        # Wait a bit to check if it started
        time.sleep(3)
        
        if process.poll() is None:  # Process is still running
            print("✅ Telegram bot started successfully!")
            return process
        else:
            print("❌ Telegram bot failed to start")
            print("")
            print("💡 POSSIBLE SOLUTIONS:")
            print("• Check if the token is correct")
            print("• Confirm that the bot is an administrator in the supergroup")
            print("• Make sure the supergroup has topics enabled")
            print("• Check if the bot has 'Manage topics' permission")
            print("• Use the web dashboard to check/change settings")
            return None
            
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        return None

def start_web_interface():
    """Starts web interface in separate thread"""
    print("🌐 Starting web interface...")
    
    def run_web():
        try:
            # Create basic web interface directly
            create_basic_web_interface()
        except Exception as e:
            print(f"❌ Error in web interface: {e}")
    
    # Start in separate thread to avoid blocking
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Wait for interface to start
    time.sleep(2)
    print("✅ Web interface started!")
    
    return web_thread

def create_basic_web_interface():
    """Creates basic web interface using Flask"""
    try:
        from flask import Flask, render_template_string
        import json
        import psutil
        
        app = Flask(__name__)
        
        # Basic HTML template
        HTML_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot - Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
                .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ddd; }
                .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; margin-top: 5px; }
                .status { padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center; }
                .status.active { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .refresh-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; }
                .refresh-btn:hover { background: #0056b3; }
                .dashboard-link { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; text-decoration: none; display: inline-block; }
                .dashboard-link:hover { background: #218838; }
            </style>
            <script>
                function refreshPage() { window.location.reload(); }
                setInterval(refreshPage, 30000); // Auto refresh every 30 seconds
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Telegram Bot</h1>
                    <p>Monitoring Dashboard</p>
                </div>
                
                <div class="status {{ status_class }}">
                    <strong>Status:</strong> {{ status_text }}
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{{ topics_count }}</div>
                        <div class="stat-label">Topics Created</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ memory_usage }}MB</div>
                        <div class="stat-label">Memory Usage</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ uptime }}</div>
                        <div class="stat-label">Uptime</div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh</button>
                    <a href="http://localhost:5000" class="dashboard-link" target="_blank">🔧 Complete Dashboard</a>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 8px;">
                    <h3>📋 Current Configuration</h3>
                    <p><strong>Token:</strong> {{ masked_token }}</p>
                    <p><strong>Supergroup:</strong> {{ backup_group_id }}</p>
                    <p><strong>Configured on:</strong> {{ config_date }}</p>
                    <p><strong>Last Update:</strong> {{ last_update }}</p>
                    <p style="color: #007bff; font-size: 14px;">💡 Use the Complete Dashboard to edit settings</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        @app.route('/')
        def dashboard():
            try:
                # Load statistics
                topics_count = 0
                try:
                    with open('bot/topics.json', 'r') as f:
                        topics = json.load(f)
                        topics_count = len(topics)
                except:
                    pass
                
                # Load configuration
                config = load_config()
                masked_token = f"{config.get('bot_token', 'N/A')[:10]}..." if config.get('bot_token') else 'Not configured'
                
                # System information
                memory_usage = round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
                
                # Check real bot status by looking for python process with telegram_bot.py
                status_text = "🔴 Bot Inactive"
                status_class = "error"
                uptime_text = "Stopped"
                
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                        if 'python' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('telegram_bot.py' in cmd for cmd in cmdline):
                                status_text = "🟢 Bot Active"
                                status_class = "active"
                                
                                # Calculate uptime
                                start_time = proc.info['create_time']
                                uptime_seconds = time.time() - start_time
                                if uptime_seconds < 60:
                                    uptime_text = f"{int(uptime_seconds)}s"
                                elif uptime_seconds < 3600:
                                    uptime_text = f"{int(uptime_seconds/60)}m"
                                else:
                                    uptime_text = f"{int(uptime_seconds/3600)}h {int((uptime_seconds%3600)/60)}m"
                                break
                except:
                    pass
                
                return render_template_string(HTML_TEMPLATE,
                    status_text=status_text,
                    status_class=status_class,
                    topics_count=topics_count,
                    memory_usage=memory_usage,
                    uptime=uptime_text,
                    masked_token=masked_token,
                    backup_group_id=config.get('backup_group_id', 'Not configured'),
                    config_date=config.get('created_at', 'N/A'),
                    last_update=datetime.now().strftime('%d/%m/%Y at %H:%M:%S')
                )
                
            except Exception as e:
                return f"<h1>Dashboard Error</h1><p>{str(e)}</p>"
        
        # Start Flask on port 8000 to avoid conflict with Streamlit
        app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
        
    except Exception as e:
        logger.error(f"Error creating web interface: {e}")

def start_streamlit_dashboard():
    """Starts Streamlit dashboard in separate process"""
    print("📊 Starting Streamlit dashboard...")
    
    try:
        # Start Streamlit as separate process
        process = subprocess.Popen(
            [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', '5000', '--server.headless', 'true'],
            env=os.environ.copy()
        )
        
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Streamlit dashboard started on port 5000!")
            return process
        else:
            print("❌ Failed to start Streamlit dashboard")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Streamlit dashboard: {e}")
        return None

def main():
    """Main function"""
    print_header()
    
    # Step 1: Check dependencies
    print_step(1, "Checking dependencies")
    if not check_dependencies():
        input("\n❌ Press Enter to exit...")
        return
    
    print()
    
    # Step 2: Initial configuration
    print_step(2, "Loading configuration")
    if not setup_initial_config():
        input("\n❌ Configuration error. Press Enter to exit...")
        return
    
    print()
    
    # Step 3: Start bot
    print_step(3, "Starting Telegram bot")
    bot_process = start_telegram_bot()
    
    print()
    
    # Step 4: Start Streamlit dashboard
    print_step(4, "Starting complete dashboard")
    streamlit_process = start_streamlit_dashboard()
    
    print()
    
    # Step 5: Start basic web interface
    print_step(5, "Starting web monitoring")
    web_thread = start_web_interface()
    
    print()
    print("=" * 60)
    print("🎉 INITIALIZATION COMPLETED!")
    print("=" * 60)
    print()
    print("📋 ACTIVE SERVICES:")
    if bot_process:
        print("   ✅ Telegram Bot: Running")
    else:
        print("   ❌ Telegram Bot: Failed")
    
    if streamlit_process:
        print("   ✅ Complete Dashboard: http://localhost:5000")
    else:
        print("   ❌ Complete Dashboard: Failed")
    
    print("   ✅ Web Monitor: http://localhost:8000")
    
    print()
    print("💡 INSTRUCTIONS:")
    print("• Use http://localhost:5000 for advanced settings")
    print("• Use http://localhost:8000 for quick monitoring")
    print("• Para parar tudo, pressione Ctrl+C")
    print()
    
    # Tenta abrir dashboard no navegador
    try:
        webbrowser.open('http://localhost:5000')
    except:
        pass
    
    # Mantém programa rodando
    try:
        while True:
            time.sleep(10)
            # Verifica se processos ainda estão rodando
            if bot_process and bot_process.poll() is not None:
                print("\n⚠️ Bot do Telegram parou de funcionar!")
                
            if streamlit_process and streamlit_process.poll() is not None:
                print("\n⚠️ Dashboard Streamlit parou de funcionar!")
                
    except KeyboardInterrupt:
        print("\n")
        print("🛑 Parando serviços...")
        
        if bot_process:
            try:
                bot_process.terminate()
                bot_process.wait(timeout=5)
                print("✅ Bot do Telegram parado")
            except:
                try:
                    bot_process.kill()
                except:
                    pass
        
        if streamlit_process:
            try:
                streamlit_process.terminate()
                streamlit_process.wait(timeout=5)
                print("✅ Dashboard Streamlit parado")
            except:
                try:
                    streamlit_process.kill()
                except:
                    pass
        
        print("👋 Até mais!")

if __name__ == "__main__":
    main()
