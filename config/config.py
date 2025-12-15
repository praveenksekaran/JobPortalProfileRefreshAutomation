"""
Configuration for Job Portal Profile Refresh Automation
"""

import os

# AWS Configuration
AWS_CONFIG = {
    'region': os.getenv('MY_AWS_REGION', 'us-east-1'),
    'secret_name': os.getenv('MY_SECRET_NAME', 'job-portal-credentials'),
}

# Portal Configuration
PORTALS = {
    'linkedin': {
        'enabled': True,
        'url': 'https://www.linkedin.com',
        'login_url': 'https://www.linkedin.com/login',
        'field': 'about',
        'max_retries': 2,
    },
    'naukri': {
        'enabled': True,
        'url': 'https://www.naukri.com',
        'login_url': 'https://www.naukri.com/nlogin/login',
        'field': 'profile_summary',
        'max_retries': 2,
    },
    'indeed': {
        'enabled': False,
        'url': 'https://www.indeed.com',
        'login_url': 'https://secure.indeed.com/account/login',
        'field': 'skills',
        'max_retries': 2,
    },
}

# Playwright Configuration
PLAYWRIGHT_CONFIG = {
    'headless': True,
    'timeout': 30000,  # 30 seconds
    'navigation_timeout': 60000,  # 1 minute
    'slow_mo': 100,  # Delay between actions (ms)
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Bedrock Configuration
# google.gemma-3-4b-it
# anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_CONFIG = {
    'model_id': 'google.gemma-3-4b-it',
    'max_tokens': 500,
    'temperature': 0.7,
    'system_prompt': 'You are a professional profile editor. Your task is to make minimal, subtle changes to profile text to keep it fresh while preserving the original meaning and intent.',
}

# Notification Configuration
NOTIFICATIONS = {
    'from_email': os.getenv('FROM_EMAIL', 'noreply@example.com'),
    'send_on_success': False,  # Disabled for testing - requires SES verification
    'send_on_failure': False,  # Disabled for testing - requires SES verification
}

# Execution Configuration
EXECUTION = {
    'max_execution_time': 270000,  # 4.5 minutes
    'delay_between_portals': 5000,  # 5 seconds
}

# Logging Configuration
LOGGING = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'include_timestamps': True,
}
