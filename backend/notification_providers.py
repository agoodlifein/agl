"""Pluggable notification provider interfaces.

Each provider implements send_email and send_whatsapp.
The MockProvider logs attempts without actually sending - swap in
real providers (SendGrid, Twilio, etc.) when API keys are available.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base for notification delivery providers."""

    @abstractmethod
    async def send_email(self, to_email: str, subject: str, body: str) -> dict:
        """Send an email. Returns {'success': bool, 'provider_id': str|None, 'error': str|None}"""

    @abstractmethod
    async def send_whatsapp(self, to_phone: str, body: str) -> dict:
        """Send a WhatsApp message. Returns {'success': bool, 'provider_id': str|None, 'error': str|None}"""


class MockProvider(NotificationProvider):
    """Mock provider that logs notifications without sending.
    
    Replace with SendGridProvider / TwilioWhatsAppProvider when ready.
    All sends are recorded as successful for development/testing.
    """

    async def send_email(self, to_email: str, subject: str, body: str) -> dict:
        logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
        return {
            'success': True,
            'provider_id': f"mock_email_{datetime.now(timezone.utc).timestamp()}",
            'error': None,
        }

    async def send_whatsapp(self, to_phone: str, body: str) -> dict:
        logger.info(f"[MOCK WHATSAPP] To: {to_phone} | Body: {body[:80]}...")
        return {
            'success': True,
            'provider_id': f"mock_wa_{datetime.now(timezone.utc).timestamp()}",
            'error': None,
        }


# ── Future provider stubs ───────────────────────────────────────────
# class SendGridProvider(NotificationProvider):
#     def __init__(self, api_key: str): ...
#     async def send_email(self, to_email, subject, body): ...
#     async def send_whatsapp(self, to_phone, body):
#         raise NotImplementedError("SendGrid does not support WhatsApp")
#
# class TwilioWhatsAppProvider(NotificationProvider):
#     def __init__(self, account_sid: str, auth_token: str, from_number: str): ...
#     async def send_email(self, to_email, subject, body):
#         raise NotImplementedError("Twilio WhatsApp does not support email")
#     async def send_whatsapp(self, to_phone, body): ...
