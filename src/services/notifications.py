"""
Email notification service using AWS SES
Sends success/failure notifications to the user
"""

from typing import Dict, Any, List
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from config import AWS_CONFIG, NOTIFICATIONS
from src.utils.logger import Logger

logger = Logger('Notifications')


class NotificationService:
    """AWS SES notification service"""

    def __init__(self):
        self.client = boto3.client('ses', region_name=AWS_CONFIG['region'])

    def send_execution_summary(self, to_email: str, summary: Dict[str, Any]) -> None:
        """
        Send execution summary email

        Args:
            to_email: Recipient email address
            summary: Execution summary dictionary
        """
        success = summary['success']
        results = summary['results']
        start_time = summary['start_time']
        end_time = summary['end_time']
        total_duration = summary['total_duration']

        subject = '✓ Job Portal Profile Refresh - Success' if success else '✗ Job Portal Profile Refresh - Partial Failure'

        html_body = self._build_html_email(results, start_time, end_time, total_duration, success)
        text_body = self._build_text_email(results, start_time, end_time, total_duration, success)

        try:
            self._send_email(to_email, subject, html_body, text_body)
            logger.info('Notification email sent successfully', {'to_email': to_email, 'success': success})
        except Exception as error:
            logger.error('Failed to send notification email', error, {'to_email': to_email})
            # Don't raise - notification failure shouldn't break the Lambda

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> None:
        """Send email via SES"""
        try:
            self.client.send_email(
                Source=NOTIFICATIONS['from_email'],
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                        'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                    },
                },
            )
        except ClientError as error:
            logger.error('SES API error', error)
            raise

    def _build_html_email(
        self,
        results: List[Dict[str, Any]],
        start_time: int,
        end_time: int,
        total_duration: int,
        success: bool
    ) -> str:
        """Build HTML email body"""
        portal_rows = []

        for result in results:
            status = '✓ Success' if result['success'] else '✗ Failed'
            status_color = '#28a745' if result['success'] else '#dc3545'
            details = f"Updated in {result.get('duration', 0)}ms" if result['success'] else f"Error: {result.get('error', 'Unknown error')}"

            portal_rows.append(f"""
          <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">{result['portal']}</td>
            <td style="padding: 10px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{status}</td>
            <td style="padding: 10px; border: 1px solid #ddd; font-size: 12px;">{details}</td>
          </tr>
        """)

        portal_table = ''.join(portal_rows)
        status_color = '#28a745' if success else '#dc3545'

        return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Profile Refresh Summary</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
  <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

    <h2 style="color: {status_color}; margin-top: 0;">
      {'✓ Profile Refresh Completed' if success else '✗ Profile Refresh Completed with Errors'}
    </h2>

    <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid {status_color}; border-radius: 4px;">
      <p style="margin: 5px 0;"><strong>Start Time:</strong> {datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S')}</p>
      <p style="margin: 5px 0;"><strong>End Time:</strong> {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d %H:%M:%S')}</p>
      <p style="margin: 5px 0;"><strong>Total Duration:</strong> {total_duration/1000:.2f}s</p>
    </div>

    <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Portal Results</h3>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <thead>
        <tr style="background-color: #007bff; color: white;">
          <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Portal</th>
          <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Status</th>
          <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Details</th>
        </tr>
      </thead>
      <tbody>
        {portal_table}
      </tbody>
    </table>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
      <p>This is an automated notification from Job Portal Profile Refresh Automation.</p>
      <p>If you did not expect this email, please contact your administrator.</p>
    </div>

  </div>
</body>
</html>
        """

    def _build_text_email(
        self,
        results: List[Dict[str, Any]],
        start_time: int,
        end_time: int,
        total_duration: int,
        success: bool
    ) -> str:
        """Build plain text email body"""
        status_symbol = '✓' if success else '✗'
        header = f"{status_symbol} JOB PORTAL PROFILE REFRESH SUMMARY\n{'=' * 50}\n"

        execution_info = f"""
Start Time: {datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {total_duration/1000:.2f}s
\n"""

        portal_results = []
        for result in results:
            status = '✓ Success' if result['success'] else '✗ Failed'
            details = f"Duration: {result.get('duration', 0)}ms" if result['success'] else f"Error: {result.get('error', 'Unknown')}"
            portal_results.append(f"{result['portal']}: {status}\n  {details}")

        portal_text = '\n\n'.join(portal_results)
        footer = f"\n{'=' * 50}\nThis is an automated notification.\n"

        return header + execution_info + 'PORTAL RESULTS:\n\n' + portal_text + footer
