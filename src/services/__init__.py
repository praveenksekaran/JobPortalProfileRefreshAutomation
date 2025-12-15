"""AWS Services integration modules"""

from .secrets_manager import SecretsManager
from .bedrock import BedrockService
from .notifications import NotificationService

# Singleton instances
secrets_manager = SecretsManager()
bedrock_service = BedrockService()
notification_service = NotificationService()

__all__ = [
    'SecretsManager',
    'BedrockService',
    'NotificationService',
    'secrets_manager',
    'bedrock_service',
    'notification_service',
]
