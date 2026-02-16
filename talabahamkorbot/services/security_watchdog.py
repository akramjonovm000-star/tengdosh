import logging
import asyncio
from datetime import datetime
from collections import defaultdict
from bot import bot
from config import ADMIN_ID

logger = logging.getLogger(__name__)

# Simple In-Memory Storage for MVP (Ideally Redis)
# Structure: {ip: count}
_error_counts = defaultdict(int) 
_banned_ips = set()
_suspicious_agents = ["curl", "python-requests", "wget", "scrapy", "go-http-client"]

class SecurityWatchdog:
    """
    Monitors traffic for suspicious patterns and enforces bans.
    """
    
    @staticmethod
    async def report_incident(incident_type: str, ip: str, details: str):
        """
        Sends a critical alert to the Admin Telegram.
        """
        msg = (
            f"🚨 <b>XAVFSIZLIK OGOHLANTIRISHI</b>\n\n"
            f"<b>Turi:</b> {incident_type}\n"
            f"<b>IP:</b> <code>{ip}</code>\n"
            f"<b>Tafsilot:</b> {details}\n"
            f"<b>Vaqt:</b> {datetime.now().strftime('%H:%M:%S')}"
        )
        try:
            # Send to Admin (assuming ADMIN_ID is set in config or hardcoded for now)
            # You might need to add ADMIN_ID to config.py if not present
            target_id = ADMIN_ID if ADMIN_ID else "73118956" # Fallback/Example ID
            await bot.send_message(chat_id=target_id, text=msg, parse_mode="HTML")
            logger.critical(f"SECURITY ALERT SENT: {incident_type} - {ip}")
        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")

    @staticmethod
    def ban_ip(ip: str, reason: str):
        """
        Temporarily bans an IP address (In-Memory).
        """
        if ip not in _banned_ips:
            _banned_ips.add(ip)
            logger.warning(f"IP BANNED: {ip} Reason: {reason}")
            # Schedule unban after 1 hour (simple approach)
            asyncio.create_task(SecurityWatchdog._unban_later(ip))
            # Async alert
            asyncio.create_task(SecurityWatchdog.report_incident("IP BLOCKED", ip, reason))

    @staticmethod
    async def _unban_later(ip: str):
        await asyncio.sleep(3600) # 1 hour
        if ip in _banned_ips:
            _banned_ips.remove(ip)
            logger.info(f"IP Unbanned: {ip}")

    @staticmethod
    def is_banned(ip: str) -> bool:
        return ip in _banned_ips

    @staticmethod
    def check_user_agent(user_agent: str, ip: str):
        """
        Checks if User-Agent is suspicious or restricted.
        """
        ua_lower = user_agent.lower()
        
        # 1. Block Known Bots/Scrapers
        for bad_agent in _suspicious_agents:
            if bad_agent in ua_lower:
                SecurityWatchdog.ban_ip(ip, f"Suspicious User-Agent: {user_agent}")
                return False
        
        # 2. Enforce Mobile-Only Policy (User Request)
        # Allowed keywords: 'android', 'iphone', 'ipad', 'ipod', 'dart', 'flutter', 'talabahamkor', 'okhttp', 'cfnetwork'
        # Block keywords: 'windows', 'macintosh', 'x11', 'ubuntu', 'fedora' (unless they also say 'mobile' - rarely)
        
        # Strict Block for Desktop OS signatures if no mobile signature is present
        desktop_os = ["windows nt", "macintosh", "x11", "ubuntu", "fedora"]
        mobile_sig = ["android", "iphone", "ipad", "ipod", "mobile", "dart", "flutter"]
        
        is_desktop = any(os_name in ua_lower for os_name in desktop_os)
        is_mobile = any(mob in ua_lower for mob in mobile_sig)
        
        if is_desktop and not is_mobile:
             # It's a PC Browser
             # Don't ban IP immediately (could be valid user testing), just block request
             return "PC_BLOCK"
             
        return True

    @staticmethod
    def track_error(ip: str, status_code: int):
        """
        Tracks 401/403 errors. If threshold exceeded -> Alert/Ban.
        """
        if status_code in [401, 403]:
            _error_counts[ip] += 1
            if _error_counts[ip] >= 10: # 10 errors = Suspicious
                SecurityWatchdog.ban_ip(ip, "Too many authentication failures (Brute Force?)")
                _error_counts[ip] = 0 # Reset
