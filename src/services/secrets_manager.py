"""
AWS Secrets Manager integration
Retrieves credentials securely from AWS Secrets Manager
"""

import json
import time
import os
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from config import AWS_CONFIG
from src.utils.logger import Logger

logger = Logger('SecretsManager')


class SecretsManager:
    """AWS Secrets Manager client wrapper"""

    def __init__(self):
        try:
            self.client = boto3.client('secretsmanager', region_name=AWS_CONFIG['region'])
        except Exception:
            self.client = None
            logger.warn('AWS client not configured, will use local secrets.json for testing')
        self.cache: Optional[Dict[str, Any]] = None
        self.cache_timestamp: Optional[float] = None
        self.cache_ttl = 300  # 5 minutes in seconds

    def get_credentials(self) -> Dict[str, Any]:
        """
        Retrieve credentials from AWS Secrets Manager or local file

        Returns:
            Parsed credentials object
        """
        # Return cached credentials if still valid
        if self.cache and self.cache_timestamp:
            age = time.time() - self.cache_timestamp
            if age < self.cache_ttl:
                logger.debug('Using cached credentials')
                return self.cache

        # Try local secrets.json first for testing
        local_secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
        if os.path.exists(local_secrets_path):
            try:
                logger.info('Loading credentials from local secrets.json')
                with open(local_secrets_path, 'r') as f:
                    credentials = json.load(f)

                # Validate credential structure
                self._validate_credentials(credentials)

                # Cache the credentials
                self.cache = credentials
                self.cache_timestamp = time.time()

                logger.info('Successfully loaded local credentials')
                return credentials
            except Exception as error:
                logger.error('Failed to load local secrets.json', error)

        # Fall back to AWS Secrets Manager
        if not self.client:
            raise Exception('No AWS client configured and no local secrets.json found')

        try:
            logger.info('Retrieving credentials from Secrets Manager', {
                'secret_name': AWS_CONFIG['secret_name'],
            })

            response = self.client.get_secret_value(SecretId=AWS_CONFIG['secret_name'])

            if 'SecretString' not in response:
                raise ValueError('Secret value is empty or not in string format')

            credentials = json.loads(response['SecretString'])

            # Validate credential structure
            self._validate_credentials(credentials)

            # Cache the credentials
            self.cache = credentials
            self.cache_timestamp = time.time()

            logger.info('Successfully retrieved credentials')
            return credentials

        except ClientError as error:
            logger.error('Failed to retrieve credentials from Secrets Manager', error)
            raise Exception(f'Secrets Manager error: {str(error)}')
        except Exception as error:
            logger.error('Failed to retrieve credentials', error)
            raise

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Validate credential structure

        Args:
            credentials: Credentials dictionary to validate

        Raises:
            ValueError: If credentials are invalid
        """
        required_portals = ['linkedin', 'naukri', 'indeed']
        required_fields = ['email', 'password']

        for portal in required_portals:
            if portal not in credentials:
                raise ValueError(f'Missing credentials for portal: {portal}')

            for field in required_fields:
                if field not in credentials[portal]:
                    raise ValueError(f'Missing {field} for portal: {portal}')

        if 'notification_email' not in credentials:
            raise ValueError('Missing notification_email in credentials')

        logger.debug('Credentials validation passed')

    def get_portal_credentials(self, portal: str) -> Dict[str, str]:
        """
        Get credentials for a specific portal

        Args:
            portal: Portal name (linkedin, naukri, indeed)

        Returns:
            Portal credentials
        """
        credentials = self.get_credentials()

        if portal not in credentials:
            raise ValueError(f'No credentials found for portal: {portal}')

        return credentials[portal]

    def get_notification_email(self) -> str:
        """
        Get notification email

        Returns:
            Notification email address
        """
        credentials = self.get_credentials()
        return credentials['notification_email']

    def clear_cache(self) -> None:
        """Clear the credentials cache"""
        logger.debug('Clearing credentials cache')
        self.cache = None
        self.cache_timestamp = None
