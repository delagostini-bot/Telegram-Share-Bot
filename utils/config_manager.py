"""
Configuration Manager for Telegram Bot Dashboard
Handles bot token, group ID, and other settings
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

class ConfigManager:
    """Manages bot configuration settings"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.default_config = {
            'bot_token': '',
            'backup_group_id': '',
            'created_at': '',
            'last_updated': ''
        }
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            return self.default_config.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict) -> bool:
        """Save configuration to JSON file"""
        try:
            config['last_updated'] = datetime.now().isoformat()
            if not config.get('created_at'):
                config['created_at'] = config['last_updated']
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Update environment variables for the current session
            if config.get('bot_token'):
                os.environ['BOT_TOKEN'] = config['bot_token']
            if config.get('backup_group_id'):
                os.environ['BACKUP_GROUP_ID'] = config['backup_group_id']
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_current_config(self) -> Dict:
        """Get current configuration"""
        return self.load_config()
    
    def update_config(self, bot_token: str = None, backup_group_id: str = None) -> bool:
        """Update specific configuration values"""
        config = self.load_config()
        
        if bot_token is not None:
            config['bot_token'] = bot_token.strip()
        if backup_group_id is not None:
            config['backup_group_id'] = backup_group_id.strip()
        
        return self.save_config(config)
    
    def is_fully_configured(self) -> bool:
        """Check if all required configuration is present"""
        config = self.load_config()
        return bool(config.get('bot_token') and config.get('backup_group_id'))
    
    def get_config_summary(self) -> Dict:
        """Get a summary of current configuration status"""
        config = self.load_config()
        
        return {
            'is_complete': self.is_fully_configured(),
            'has_token': bool(config.get('bot_token')),
            'has_group_id': bool(config.get('backup_group_id')),
            'token_preview': config.get('bot_token', '')[:10] + '...' if config.get('bot_token') else 'Not set',
            'group_id': config.get('backup_group_id', 'Not set'),
            'last_updated': config.get('last_updated', 'Never')
        }
    
    def run_diagnostics(self) -> Dict:
        """Run configuration diagnostics"""
        config = self.load_config()
        diagnostics = {}
        
        # Check bot token format
        token = config.get('bot_token', '')
        if not token:
            diagnostics['Bot Token'] = {'status': 'error', 'message': 'Token not configured'}
        elif ':' not in token or len(token) < 40:
            diagnostics['Bot Token'] = {'status': 'warning', 'message': 'Token format seems invalid'}
        else:
            diagnostics['Bot Token'] = {'status': 'ok', 'message': 'Token format looks correct'}
        
        # Check group ID format
        group_id = config.get('backup_group_id', '')
        if not group_id:
            diagnostics['Group ID'] = {'status': 'error', 'message': 'Group ID not configured'}
        else:
            try:
                id_int = int(group_id)
                if id_int >= 0:
                    diagnostics['Group ID'] = {'status': 'warning', 'message': 'Group ID should be negative'}
                else:
                    diagnostics['Group ID'] = {'status': 'ok', 'message': 'Group ID format looks correct'}
            except ValueError:
                diagnostics['Group ID'] = {'status': 'error', 'message': 'Group ID must be a number'}
        
        # Check configuration file
        if os.path.exists(self.config_file):
            diagnostics['Config File'] = {'status': 'ok', 'message': 'Configuration file exists'}
        else:
            diagnostics['Config File'] = {'status': 'warning', 'message': 'Using default configuration'}
        
        return diagnostics