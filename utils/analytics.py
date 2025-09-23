"""
Analytics Manager for Telegram Bot Dashboard
Provides statistics and analytics for bot activity - REAL DATA ONLY
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AnalyticsManager:
    """Manages analytics and statistics for the bot - real data only"""
    
    def __init__(self):
        self.topics_file = 'bot/topics.json'
        self.stats_file = 'bot/stats.json'
        self.logs_file = 'bot/activity_logs.json'
        # Garante que os arquivos existam
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Cria arquivos com estrutura mínima se não existirem."""
        # stats.json
        if not os.path.exists(self.stats_file):
            default_stats = {
                "total_messages": 0,
                "today_messages": 0,
                "week_messages": 0,
                "topics": {}
            }
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(default_stats, f, indent=2, ensure_ascii=False)

        # activity_logs.json
        if not os.path.exists(self.logs_file):
            os.makedirs(os.path.dirname(self.logs_file), exist_ok=True)
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the dashboard"""
        try:
            # Load topics
            topics_count = 0
            if os.path.exists(self.topics_file):
                with open(self.topics_file, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
                    topics_count = len(topics)
            
            # Load real activity stats if available
            total_messages = self._get_total_messages()
            today_messages = self._get_today_messages()
            active_sources = topics_count  # Real count from topics
            
            return {
                'total_messages': total_messages,
                'total_topics': topics_count,
                'today_messages': today_messages,
                'active_sources': active_sources,
                'week_messages': self._get_week_messages()
            }
        except Exception as e:
            print(f"Error getting summary stats: {e}")
            return {
                'total_messages': 0,
                'total_topics': 0,
                'today_messages': 0,
                'active_sources': 0,
                'week_messages': 0
            }
    
    def get_daily_activity(self, days: int = 7) -> List[Dict]:
        """Get daily activity data for the last N days - REAL DATA ONLY"""
        try:
            if not os.path.exists(self.logs_file):
                return []

            with open(self.logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not isinstance(logs, list):
                return []

            today = datetime.now().date()
            start_date = today - timedelta(days=days-1)
            daily_counts = { (start_date + timedelta(days=i)).isoformat(): 0 for i in range(days) }

            for log in logs:
                ts = log.get('timestamp')
                if not ts:
                    continue
                try:
                    log_date = datetime.fromisoformat(ts).date().isoformat()
                    if log_date in daily_counts:
                        daily_counts[log_date] += 1
                except Exception:
                    continue

            return [{"date": date, "count": count} for date, count in daily_counts.items()]

        except Exception as e:
            print(f"Error getting daily activity: {e}")
            return []

    def get_hourly_activity(self, hours: int = 24) -> List[Dict]:
        """Get hourly activity data for the last N hours - REAL DATA ONLY"""
        try:
            if not os.path.exists(self.logs_file):
                return []

            with open(self.logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not isinstance(logs, list):
                return []

            now = datetime.now()
            hourly_counts = {i: 0 for i in range(24)}  # 0-23

            for log in logs:
                ts = log.get('timestamp')
                if not ts:
                    continue
                try:
                    log_dt = datetime.fromisoformat(ts)
                    # Considera apenas as últimas 24 horas
                    if (now - log_dt).total_seconds() <= 24 * 3600:
                        hour = log_dt.hour
                        hourly_counts[hour] += 1
                except Exception:
                    continue

            return [{"hour": f"{h:02d}:00", "count": count} for h, count in hourly_counts.items()]

        except Exception as e:
            print(f"Error getting hourly activity: {e}")
            return []

    def get_media_types_distribution(self) -> Dict[str, int]:
        """Get distribution of media types - REAL DATA ONLY"""
        try:
            if not os.path.exists(self.logs_file):
                return {}

            with open(self.logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not isinstance(logs, list):
                return {}

            media_counts = {}

            for log in logs:
                media_type = log.get('media_type', 'unknown')
                media_counts[media_type] = media_counts.get(media_type, 0) + 1

            return media_counts

        except Exception as e:
            print(f"Error getting media types distribution: {e}")
            return {}

    def get_top_sources(self, limit: int = 10) -> List[Dict]:
        """Get top source groups - REAL DATA ONLY from topics"""
        try:
            if os.path.exists(self.topics_file):
                with open(self.topics_file, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
                
                sources = []
                for topic_name, thread_id in topics.items():
                    sources.append({
                        'source': topic_name,
                        'thread_id': thread_id,
                        'status': 'Active'
                    })
                
                return sources[:limit]
            
            return []
        except Exception as e:
            print(f"Error getting top sources: {e}")
            return []
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent activity logs - REAL DATA ONLY"""
        try:
            if os.path.exists(self.logs_file):
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                
                if isinstance(logs, list):
                    return logs[-limit:] if len(logs) > limit else logs
                    
            return []
        except Exception as e:
            print(f"Error getting recent logs: {e}")
            return []
    
    def get_topics_timeline(self) -> List[Dict]:
        """Get topics creation timeline - REAL DATA ONLY"""
        try:
            if os.path.exists(self.topics_file):
                with open(self.topics_file, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
                
                file_mtime = os.path.getmtime(self.topics_file)
                last_modified = datetime.fromtimestamp(file_mtime)
                
                timeline = []
                for topic_name, thread_id in topics.items():
                    timeline.append({
                        'topic': topic_name,
                        'thread_id': thread_id,
                        'last_updated': last_modified,
                        'last_updated_str': last_modified.strftime('%Y-%m-%d %H:%M')
                    })
                
                timeline.sort(key=lambda x: x['thread_id'])
                return timeline
            
            return []
        except Exception as e:
            print(f"Error getting topics timeline: {e}")
            return []
    
    def _get_total_messages(self) -> int:
        """Get total messages processed - REAL DATA ONLY"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                return stats.get('total_messages', 0)
        except Exception:
            pass
        return 0
    
    def _get_today_messages(self) -> int:
        """Get today's message count - REAL DATA ONLY"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                return stats.get('today_messages', 0)
        except Exception:
            pass
        return 0
    
    def _get_week_messages(self) -> int:
        """Get this week's message count - REAL DATA ONLY"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                return stats.get('week_messages', 0)
        except Exception:
            pass
        return 0
    
    def get_topic_media_count(self, topic_name: str) -> int:
        """Get the number of shared media for a specific topic - REAL DATA ONLY"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                topic_stats = stats.get('topics', {})
                return topic_stats.get(topic_name, 0)
            return 0
        except Exception:
            return 0