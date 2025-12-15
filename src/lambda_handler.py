"""
AWS Lambda Handler for Job Portal Profile Refresh Automation
Orchestrates profile updates across LinkedIn, Naukri, and Indeed
"""

import asyncio
import time
import json
from typing import Dict, Any, List

from config import PORTALS, EXECUTION
from src.utils.logger import Logger
from src.services import secrets_manager, notification_service
from src.portals import linkedin_automation, naukri_automation, indeed_automation

logger = Logger('Lambda')

# Portal automation mapping
PORTAL_AUTOMATIONS = {
    'linkedin': linkedin_automation,
    'naukri': naukri_automation,
    'indeed': indeed_automation,
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Response dictionary
    """
    # Run async handler
    return asyncio.run(async_handler(event, context))


async def async_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Async Lambda handler

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Response dictionary
    """
    execution_start_time = int(time.time() * 1000)

    logger.info('Job Portal Profile Refresh Automation started', {
        'request_id': context.request_id if hasattr(context, 'request_id') else 'local',
        'event': event,
    })

    credentials = None
    notification_email = None

    try:
        # Retrieve credentials from Secrets Manager
        credentials = secrets_manager.get_credentials()
        notification_email = credentials['notification_email']

        logger.info('Credentials retrieved successfully')

        # Execute profile updates for each enabled portal
        results = await execute_portal_updates(credentials)

        # Calculate execution summary
        execution_end_time = int(time.time() * 1000)
        total_duration = execution_end_time - execution_start_time
        overall_success = all(r['success'] for r in results)

        summary = {
            'success': overall_success,
            'results': results,
            'start_time': execution_start_time,
            'end_time': execution_end_time,
            'total_duration': total_duration,
        }

        logger.execution_summary(summary)

        # Send notification email
        from config import NOTIFICATIONS
        if NOTIFICATIONS['send_on_success'] or not overall_success:
            notification_service.send_execution_summary(notification_email, summary)

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'All portals updated successfully' if overall_success else 'Some portals failed to update',
                'summary': summary,
            }),
        }

    except Exception as error:
        logger.error('Fatal error in Lambda execution', error)

        # Send failure notification if possible
        from config import NOTIFICATIONS
        if notification_email and NOTIFICATIONS['send_on_failure']:
            try:
                execution_end_time = int(time.time() * 1000)
                summary = {
                    'success': False,
                    'results': [{'portal': 'System', 'success': False, 'error': str(error)}],
                    'start_time': execution_start_time,
                    'end_time': execution_end_time,
                    'total_duration': execution_end_time - execution_start_time,
                }

                notification_service.send_execution_summary(notification_email, summary)
            except Exception as notification_error:
                logger.error('Failed to send failure notification', notification_error)

        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Lambda execution failed',
                'error': str(error),
            }),
        }


async def execute_portal_updates(credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute profile updates for all enabled portals

    Args:
        credentials: All portal credentials

    Returns:
        List of execution results
    """
    results = []
    enabled_portals = get_enabled_portals()

    logger.info(f'Executing updates for {len(enabled_portals)} portals', {
        'portals': enabled_portals,
    })

    for portal_name in enabled_portals:
        try:
            logger.info(f'Starting {portal_name} automation')

            # Get portal credentials
            portal_credentials = credentials.get(portal_name)
            if not portal_credentials:
                raise ValueError(f'No credentials found for portal: {portal_name}')

            # Get portal automation module
            automation = PORTAL_AUTOMATIONS.get(portal_name)
            if not automation:
                raise ValueError(f'No automation module found for portal: {portal_name}')

            # Execute portal automation with retry logic
            result = await execute_with_retry(
                automation.execute(portal_credentials),
                PORTALS[portal_name]['max_retries'],
                portal_name
            )

            results.append(result)

            # Delay between portals to avoid rate limiting
            if EXECUTION['delay_between_portals'] > 0:
                await asyncio.sleep(EXECUTION['delay_between_portals'] / 1000)

        except Exception as error:
            logger.error(f'Fatal error executing {portal_name} automation', error)

            results.append({
                'portal': portal_name,
                'success': False,
                'error': str(error),
                'duration': 0,
            })

    return results


def get_enabled_portals() -> List[str]:
    """
    Get list of enabled portals from configuration

    Returns:
        List of enabled portal names
    """
    return [portal_name for portal_name, config in PORTALS.items() if config['enabled']]


async def execute_with_retry(coroutine, max_retries: int, context: str):
    """
    Execute coroutine with retry logic

    Args:
        coroutine: Async coroutine to execute
        max_retries: Maximum number of retries
        context: Context for logging

    Returns:
        Coroutine result
    """
    last_error = None

    for attempt in range(1, max_retries + 2):
        try:
            logger.info(f'{context}: Attempt {attempt}/{max_retries + 1}')
            return await coroutine

        except Exception as error:
            last_error = error
            logger.warn(f'{context}: Attempt {attempt} failed', {
                'error': str(error),
                'will_retry': attempt <= max_retries,
            })

            if attempt <= max_retries:
                # Exponential backoff: 2^attempt seconds
                backoff_time = 2 ** attempt
                logger.info(f'{context}: Retrying in {backoff_time}s')
                await asyncio.sleep(backoff_time)

    # All retries exhausted
    raise last_error


# Local testing
if __name__ == '__main__':
    import sys
    import os

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info('Running in local test mode')

    # Mock Lambda context
    class MockContext:
        request_id = 'local-test-' + str(int(time.time() * 1000))
        function_name = 'job-portal-refresh-local'

    # Mock Lambda event
    mock_event = {}
    mock_context = MockContext()

    try:
        result = lambda_handler(mock_event, mock_context)
        print('\n=== EXECUTION RESULT ===')
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print('\n=== EXECUTION FAILED ===')
        print(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
