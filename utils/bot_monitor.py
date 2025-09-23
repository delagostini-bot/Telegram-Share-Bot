"""
Bot Monitor for Telegram Bot Dashboard
Monitors bot status, performance, and provides control functions
"""

import os
import subprocess
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class BotMonitor:
    """Monitors and controls the Telegram bot process"""
    
    def __init__(self):
        self.bot_script_path = 'bot/telegram_bot.py'
        self.bot_process = None
        self.start_time = None
    
    def is_bot_running(self) -> bool:
        """Check if the bot process is currently running"""
        try:
            # Check for existing bot processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and self.bot_script_path in ' '.join(proc.info['cmdline']):
                        self.bot_process = proc
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False
    
    def get_bot_status(self) -> Dict:
        """Get comprehensive bot status information"""
        is_running = self.is_bot_running()
        
        status = {
            'is_running': is_running,
            'uptime': self.get_uptime() if is_running else None,
            'memory_usage': self.get_memory_usage() if is_running else None,
            'cpu_usage': self.get_cpu_usage() if is_running else None,
            'process_id': self.bot_process.pid if self.bot_process else None,
            'last_check': datetime.now().isoformat()
        }
        
        return status
    
    def get_uptime(self) -> str:
        """Get bot uptime as a formatted string"""
        if not self.bot_process:
            return "Not running"
        
        try:
            create_time = datetime.fromtimestamp(self.bot_process.create_time())
            uptime = datetime.now() - create_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return "Unknown"
    
    def get_memory_usage(self) -> Optional[float]:
        """Get bot memory usage in MB"""
        if not self.bot_process:
            return None
        
        try:
            memory_info = self.bot_process.memory_info()
            return round(memory_info.rss / 1024 / 1024, 2)  # Convert to MB
        except Exception:
            return None
    
    def get_cpu_usage(self) -> Optional[float]:
        """Get bot CPU usage percentage"""
        if not self.bot_process:
            return None
        
        try:
            return round(self.bot_process.cpu_percent(interval=1), 2)
        except Exception:
            return None
    
    def start_bot(self) -> bool:
        """Start the bot process"""
        if self.is_bot_running():
            return True  # Already running
        
        try:
            # Ensure bot directory exists
            bot_dir = os.path.dirname(self.bot_script_path)
            if not os.path.exists(bot_dir):
                os.makedirs(bot_dir, exist_ok=True)
            
            # Check if bot script exists
            if not os.path.exists(self.bot_script_path):
                print(f"Bot script not found at {self.bot_script_path}")
                return False
            
            # Start the bot process
            process = subprocess.Popen(
                ['/usr/bin/python3', self.bot_script_path],
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if process.poll() is None:  # Process is still running
                self.start_time = datetime.now()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error starting bot: {e}")
            return False
    
    def stop_bot(self) -> bool:
        """Stop the bot process"""
        if not self.is_bot_running():
            return True  # Already stopped
        
        try:
            if self.bot_process:
                self.bot_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.bot_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    self.bot_process.kill()
                    self.bot_process.wait()
                
                self.bot_process = None
                self.start_time = None
                return True
        except Exception as e:
            print(f"Error stopping bot: {e}")
            return False
    
    def restart_bot(self) -> bool:
        """Restart the bot process"""
        if not self.stop_bot():
            return False
        
        time.sleep(2)  # Wait a moment between stop and start
        return self.start_bot()
    
    def get_system_info(self) -> Dict:
        """Get system performance information"""
        try:
            # System stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Bot-specific stats
            files_processed = self.get_files_processed_count()
            error_count = self.get_error_count()
            last_activity = self.get_last_activity()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / 1024**3, 2),
                'memory_total_gb': round(memory.total / 1024**3, 2),
                'disk_percent': disk.percent,
                'disk_used_gb': round(disk.used / 1024**3, 2),
                'disk_total_gb': round(disk.total / 1024**3, 2),
                'files_processed': files_processed,
                'error_count': error_count,
                'last_activity': last_activity
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return {}
    
    def get_files_processed_count(self) -> int:
        """Get count of files processed (placeholder - implement based on your logging)"""
        # This would typically read from a log file or database
        # For now, return a placeholder value
        try:
            # Could read from a stats file if you implement logging
            stats_file = 'bot/stats.json'
            if os.path.exists(stats_file):
                import json
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                return stats.get('files_processed', 0)
        except Exception:
            pass
        return 0
    
    def get_error_count(self) -> int:
        """Get count of errors (placeholder - implement based on your logging)"""
        # This would typically read from error logs
        # For now, return a placeholder value
        return 0
    
    def get_last_activity(self) -> str:
        """Get timestamp of last bot activity"""
        try:
            # Could check modification time of topics.json as a proxy for activity
            topics_file = 'bot/topics.json'
            if os.path.exists(topics_file):
                mtime = os.path.getmtime(topics_file)
                last_mod = datetime.fromtimestamp(mtime)
                time_diff = datetime.now() - last_mod
                
                if time_diff.days > 0:
                    return f"{time_diff.days} days ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    return f"{hours} hours ago"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    return f"{minutes} minutes ago"
                else:
                    return "Just now"
        except Exception:
            pass
        return "Unknown"
    
    def get_topics_count(self) -> int:
        """Get number of topics created"""
        try:
            topics_file = 'bot/topics.json'
            if os.path.exists(topics_file):
                import json
                with open(topics_file, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
                return len(topics)
        except Exception:
            pass
        return 0