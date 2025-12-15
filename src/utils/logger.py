"""
Logging utility for audit trail and debugging
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from config import LOGGING

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}


class Logger:
    """Structured logger for the application"""

    def __init__(self, context: str = 'APP'):
        self.context = context
        self.level = LOG_LEVELS.get(LOGGING['level'], logging.INFO)

        # Configure Python logging
        logging.basicConfig(
            level=self.level,
            format='%(message)s'
        )
        self.logger = logging.getLogger(context)

    def _should_log(self, level: str) -> bool:
        """Check if message should be logged at given level"""
        return LOG_LEVELS.get(level, logging.INFO) >= self.level

    def _format_message(self, level: str, message: str, meta: Optional[Dict[str, Any]] = None) -> str:
        """Format log message as JSON"""
        timestamp = datetime.utcnow().isoformat() if LOGGING['include_timestamps'] else ''

        log_entry = {
            'timestamp': timestamp,
            'level': level.upper(),
            'context': self.context,
            'message': message,
        }

        if meta:
            log_entry.update(meta)

        return json.dumps(log_entry)

    def debug(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message"""
        if self._should_log('DEBUG'):
            self.logger.debug(self._format_message('debug', message, meta or {}))

    def info(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Log info message"""
        if self._should_log('INFO'):
            self.logger.info(self._format_message('info', message, meta or {}))

    def warn(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message"""
        if self._should_log('WARNING'):
            self.logger.warning(self._format_message('warning', message, meta or {}))

    def error(self, message: str, error: Optional[Exception] = None, meta: Optional[Dict[str, Any]] = None) -> None:
        """Log error message"""
        if self._should_log('ERROR'):
            error_meta = meta or {}

            if error:
                error_meta['error'] = {
                    'message': str(error),
                    'type': type(error).__name__,
                }

            self.logger.error(self._format_message('error', message, error_meta))

    def portal_start(self, portal: str) -> None:
        """Log portal automation start"""
        self.info(f'Starting automation for portal: {portal}', {'portal': portal})

    def portal_success(self, portal: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log portal automation success"""
        meta = {'portal': portal}
        if details:
            meta.update(details)
        self.info(f'Successfully updated portal: {portal}', meta)

    def portal_failure(self, portal: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """Log portal automation failure"""
        meta = {'portal': portal}
        if details:
            meta.update(details)
        self.error(f'Failed to update portal: {portal}', error, meta)

    def execution_summary(self, summary: Dict[str, Any]) -> None:
        """Log execution summary"""
        self.info('Execution summary', summary)
