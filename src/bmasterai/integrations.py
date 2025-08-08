
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import sqlite3
import os
from datetime import datetime, timezone
import base64
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        pass

class SlackConnector(BaseConnector):
    """Slack integration for sending messages and notifications"""

    def __init__(self, webhook_url: str, bot_token: Optional[str] = None):
        super().__init__({'webhook_url': webhook_url, 'bot_token': bot_token})
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bot_token}' if bot_token else None
        }

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            response = self.send_message("🤖 BMasterAI connection test", channel="#general")
            return {'success': True, 'message': 'Connected to Slack successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_message(self, message: str, channel: str = "#general", username: str = "BMasterAI") -> Dict[str, Any]:
        payload = {
            'text': message,
            'channel': channel,
            'username': username,
            'icon_emoji': ':robot_face:'
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return {'success': True, 'response': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        message = f"🚨 *Alert: {alert_data.get('metric_name', 'Unknown')}*\n"
        message += f"Current Value: {alert_data.get('current_value', 'N/A')}\n"
        message += f"Threshold: {alert_data.get('threshold', 'N/A')}\n"
        message += f"Time: {alert_data.get('timestamp', 'N/A')}"

        return self.send_message(message, channel="#alerts")

class EmailConnector(BaseConnector):
    """Email integration for notifications and reports"""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        super().__init__({
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password,
            'use_tls': use_tls
        })
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.quit()
            return {'success': True, 'message': 'Email connection successful'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_email(self, to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None) -> Dict[str, Any]:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)

            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            return {'success': True, 'message': f'Email sent to {len(to_emails)} recipients'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_report(self, to_emails: List[str], report_data: Dict[str, Any]) -> Dict[str, Any]:
        subject = f"BMasterAI Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        body = f"""
BMasterAI System Report

Generated: {report_data.get('timestamp', 'N/A')}

System Health:
- Active Agents: {report_data.get('active_agents', 0)}
- Total Agents: {report_data.get('total_agents', 0)}
- CPU Usage: {report_data.get('system_metrics', {}).get('cpu', {}).get('avg', 'N/A')}%
- Memory Usage: {report_data.get('system_metrics', {}).get('memory', {}).get('avg', 'N/A')}%

Recent Alerts: {len(report_data.get('recent_alerts', []))}

Best regards,
BMasterAI System
"""

        return self.send_email(to_emails, subject, body)

class DatabaseConnector(BaseConnector):
    """Database integration for data storage and retrieval"""

    def __init__(self, db_type: str = "sqlite", connection_string: str = "bmasterai.db", **kwargs):
        super().__init__({'db_type': db_type, 'connection_string': connection_string, **kwargs})
        self.db_type = db_type
        self.connection_string = connection_string
        self.connection = None

        if db_type == "sqlite":
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.connection_string)
            cursor = conn.cursor()

            # Create agents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    metadata TEXT
                )
            ''')

            # Create tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    name TEXT,
                    status TEXT,
                    duration_ms REAL,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')

            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    value REAL,
                    labels TEXT,
                    timestamp TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing SQLite database: {e}")

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(self.connection_string)
                conn.close()
                return {'success': True, 'message': 'Database connection successful'}
            else:
                return {'success': False, 'error': 'Unsupported database type'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def store_agent_data(self, agent_id: str, name: str, status: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.connection_string)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO agents (id, name, status, created_at, last_activity, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                agent_id, name, status, 
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                json.dumps(metadata or {})
            ))

            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Agent data stored successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def store_task_data(self, task_id: str, agent_id: str, name: str, status: str, 
                       duration_ms: Optional[float] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.connection_string)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO tasks (id, agent_id, name, status, duration_ms, created_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, agent_id, name, status, duration_ms,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat() if status == 'completed' else None,
                json.dumps(metadata or {})
            ))

            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Task data stored successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_agent_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.connection_string)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM tasks WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?
            ''', (agent_id, limit))

            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return results
        except Exception as e:
            print(f"Error getting agent history: {e}")
            return []

class WebhookConnector(BaseConnector):
    """Generic webhook integration for external services"""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None, auth_token: Optional[str] = None):
        super().__init__({'webhook_url': webhook_url, 'headers': headers, 'auth_token': auth_token})
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}

        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            test_payload = {'test': True, 'timestamp': datetime.now(timezone.utc).isoformat()}
            response = requests.post(self.webhook_url, json=test_payload, headers=self.headers, timeout=10)
            return {'success': response.status_code < 400, 'status_code': response.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(self.webhook_url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return {'success': True, 'status_code': response.status_code, 'response': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class DiscordConnector(BaseConnector):
    """Discord integration for notifications"""

    def __init__(self, webhook_url: str):
        super().__init__({'webhook_url': webhook_url})
        self.webhook_url = webhook_url

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            response = self.send_message("🤖 BMasterAI connection test")
            return {'success': response['success'], 'message': 'Discord connection test completed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_message(self, message: str, username: str = "BMasterAI") -> Dict[str, Any]:
        payload = {
            'content': message,
            'username': username,
            'avatar_url': 'https://cdn-icons-png.flaticon.com/512/4712/4712027.png'
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return {'success': True, 'response': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_embed(self, title: str, description: str, color: int = 0x00ff00, fields: List[Dict[str, str]] = None) -> Dict[str, Any]:
        embed = {
            'title': title,
            'description': description,
            'color': color,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'footer': {'text': 'BMasterAI'}
        }

        if fields:
            embed['fields'] = fields

        payload = {'embeds': [embed]}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return {'success': True, 'response': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class TeamsConnector(BaseConnector):
    """Microsoft Teams integration"""

    def __init__(self, webhook_url: str):
        super().__init__({'webhook_url': webhook_url})
        self.webhook_url = webhook_url

    def connect(self) -> bool:
        return self.test_connection()['success']

    def test_connection(self) -> Dict[str, Any]:
        try:
            response = self.send_message("🤖 BMasterAI connection test")
            return {'success': response['success'], 'message': 'Teams connection test completed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_message(self, message: str, title: str = "BMasterAI Notification") -> Dict[str, Any]:
        payload = {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': '0076D7',
            'summary': title,
            'sections': [{
                'activityTitle': title,
                'activitySubtitle': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'activityImage': 'https://cdn-icons-png.flaticon.com/512/4712/4712027.png',
                'text': message,
                'markdown': True
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return {'success': True, 'response': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class IntegrationManager:
    """Manages all integrations and provides unified interface"""

    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.active_integrations: List[str] = []

    def add_connector(self, name: str, connector: BaseConnector) -> Dict[str, Any]:
        try:
            if connector.connect():
                self.connectors[name] = connector
                self.active_integrations.append(name)
                return {'success': True, 'message': f'{name} connector added successfully'}
            else:
                return {'success': False, 'error': f'Failed to connect to {name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def remove_connector(self, name: str) -> Dict[str, Any]:
        if name in self.connectors:
            del self.connectors[name]
            if name in self.active_integrations:
                self.active_integrations.remove(name)
            return {'success': True, 'message': f'{name} connector removed'}
        return {'success': False, 'error': f'{name} connector not found'}

    def get_connector(self, name: str) -> Optional[BaseConnector]:
        return self.connectors.get(name)

    def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, connector in self.connectors.items():
            results[name] = connector.test_connection()
        return results

    def broadcast_message(self, message: str, exclude: List[str] = None) -> Dict[str, Dict[str, Any]]:
        exclude = exclude or []
        results = {}

        for name, connector in self.connectors.items():
            if name in exclude:
                continue

            try:
                if hasattr(connector, 'send_message'):
                    results[name] = connector.send_message(message)
                else:
                    results[name] = {'success': False, 'error': 'Connector does not support messaging'}
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}

        return results

    def send_alert_to_all(self, alert_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        results = {}

        for name, connector in self.connectors.items():
            try:
                if hasattr(connector, 'send_alert'):
                    results[name] = connector.send_alert(alert_data)
                elif hasattr(connector, 'send_message'):
                    message = f"Alert: {alert_data.get('metric_name', 'Unknown')} - {alert_data.get('message', '')}"
                    results[name] = connector.send_message(message)
                else:
                    results[name] = {'success': False, 'error': 'Connector does not support alerts'}
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}

        return results

    def get_status(self) -> Dict[str, Any]:
        return {
            'total_connectors': len(self.connectors),
            'active_integrations': self.active_integrations,
            'connector_status': {name: connector.test_connection() for name, connector in self.connectors.items()}
        }

# Global integration manager
_integration_manager = None

def get_integration_manager() -> IntegrationManager:
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager
