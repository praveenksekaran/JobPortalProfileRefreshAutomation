"""
Playwright utility functions
Helper functions for browser automation
"""

import asyncio
import random
from typing import Optional, Dict, Any, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import PLAYWRIGHT_CONFIG
from .logger import Logger

logger = Logger('Playwright')


async def launch_browser() -> Tuple[Browser, BrowserContext, Page]:
    """
    Launch a browser instance

    Returns:
        Tuple of (browser, context, page)
    """
    try:
        logger.debug('Launching browser')

        playwright = await async_playwright().start()

        browser = await playwright.chromium.launch(
            headless=PLAYWRIGHT_CONFIG['headless'],
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process',
                '--no-zygote',
            ],
        )

        context = await browser.new_context(
            user_agent=PLAYWRIGHT_CONFIG['user_agent'],
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='Asia/Kolkata',
        )

        # Set default timeouts
        context.set_default_timeout(PLAYWRIGHT_CONFIG['timeout'])
        context.set_default_navigation_timeout(PLAYWRIGHT_CONFIG['navigation_timeout'])

        page = await context.new_page()

        logger.info('Browser launched successfully')

        return browser, context, page

    except Exception as error:
        logger.error('Failed to launch browser', error)
        raise


async def close_browser(browser: Optional[Browser]) -> None:
    """Close browser instance"""
    try:
        if browser:
            await browser.close()
            logger.debug('Browser closed')
    except Exception as error:
        logger.error('Error closing browser', error)


async def human_delay(ms: Optional[int] = None) -> None:
    """
    Human-like delay

    Args:
        ms: Milliseconds to wait (random 1-3s if not provided)
    """
    delay = ms if ms is not None else random.uniform(1000, 3000)
    await asyncio.sleep(delay / 1000)


async def human_type(page: Page, selector: str, text: str) -> None:
    """
    Type text with human-like speed

    Args:
        page: Playwright page object
        selector: Element selector
        text: Text to type
    """
    await page.click(selector)
    await human_delay(500)

    # Type with random delays between characters
    for char in text:
        await page.type(selector, char, delay=random.uniform(50, 150))

    await human_delay(300)


async def wait_for_selector(
    page: Page,
    selector: str,
    max_attempts: int = 3,
    timeout: Optional[int] = None
) -> bool:
    """
    Wait for element with retry logic

    Args:
        page: Playwright page object
        selector: Element selector
        max_attempts: Maximum retry attempts
        timeout: Timeout in milliseconds

    Returns:
        True if element found
    """
    timeout_ms = timeout or PLAYWRIGHT_CONFIG['timeout']

    for i in range(max_attempts):
        try:
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except Exception as error:
            if i == max_attempts - 1:
                logger.error(
                    f'Element not found after {max_attempts} attempts',
                    error,
                    {'selector': selector}
                )
                return False

            logger.warn(f'Attempt {i + 1} failed, retrying...', {'selector': selector})
            await human_delay(2000)

    return False


async def safe_click(page: Page, selector: str) -> None:
    """
    Safe click with wait

    Args:
        page: Playwright page object
        selector: Element selector
    """
    await wait_for_selector(page, selector)
    await page.click(selector)
    await human_delay(PLAYWRIGHT_CONFIG['slow_mo'])


async def get_text_content(page: Page, selector: str) -> Optional[str]:
    """
    Get text content safely

    Args:
        page: Playwright page object
        selector: Element selector

    Returns:
        Text content or None
    """
    try:
        element = await page.query_selector(selector)
        if not element:
            return None

        text = await element.text_content()
        return text.strip() if text else None

    except Exception as error:
        logger.error('Failed to get text content', error, {'selector': selector})
        return None


async def take_screenshot(page: Page, name: str) -> None:
    """
    Take screenshot for debugging

    Args:
        page: Playwright page object
        name: Screenshot name
    """
    try:
        import time
        timestamp = int(time.time() * 1000)
        filename = f'/tmp/{name}-{timestamp}.png'
        await page.screenshot(path=filename, full_page=True)
        logger.debug(f'Screenshot saved: {filename}')
    except Exception as error:
        logger.error('Failed to take screenshot', error)


async def detect_login_errors(page: Page) -> Optional[Dict[str, str]]:
    """
    Handle common login errors

    Args:
        page: Playwright page object

    Returns:
        Error details or None
    """
    error_selectors = [
        {'selector': '[role="alert"]', 'type': 'alert'},
        {'selector': '.error-message', 'type': 'error'},
        {'selector': '.alert-danger', 'type': 'danger'},
        {'selector': '[data-test="error"]', 'type': 'test-error'},
    ]

    for error_info in error_selectors:
        try:
            error_element = await page.query_selector(error_info['selector'])
            if error_element:
                error_text = await error_element.text_content()
                return {
                    'type': error_info['type'],
                    'message': error_text.strip() if error_text else ''
                }
        except Exception:
            continue

    return None
