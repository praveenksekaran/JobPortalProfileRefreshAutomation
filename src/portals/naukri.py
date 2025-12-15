"""
Naukri Profile Automation
Automates login and "Profile Summary" section update on Naukri.com
"""

import time
from typing import Dict, Any

from config import PORTALS
from src.utils.logger import Logger
from src.services.bedrock import BedrockService
from src.utils.playwright_helpers import (
    launch_browser,
    close_browser,
    human_delay,
    human_type,
    wait_for_selector,
    safe_click,
    take_screenshot,
    detect_login_errors,
)

logger = Logger('Naukri')


class NaukriAutomation:
    """Naukri profile automation handler"""

    def __init__(self):
        self.bedrock = BedrockService()

    async def execute(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute Naukri profile update

        Args:
            credentials: Naukri credentials {email, password}

        Returns:
            Execution result dictionary
        """
        start_time = int(time.time() * 1000)
        browser = None

        try:
            logger.portal_start('Naukri')

            # Launch browser
            browser, context, page = await launch_browser()

            # Login
            await self._login(page, credentials)
            logger.info('Naukri login successful')

            # Navigate to profile page
            await self._navigate_to_profile(page)
            logger.info('Navigated to profile page')

            # Read current Profile Summary
            current_summary = await self._read_profile_summary(page)
            logger.info('Read current Profile Summary', {'length': len(current_summary)})

            # Mutate content using AI
            new_summary = self.bedrock.mutate_content(current_summary, 'Naukri Profile Summary')

            # Validate mutation
            if not self.bedrock.validate_mutation(current_summary, new_summary):
                raise Exception('Content mutation validation failed')

            # Update Profile Summary
            await self._update_profile_summary(page, new_summary)
            logger.info('Updated Profile Summary successfully')

            duration = int(time.time() * 1000) - start_time
            logger.portal_success('Naukri', {'duration': duration})

            return {
                'portal': 'Naukri',
                'success': True,
                'duration': duration,
                'details': {'content_length': len(new_summary)},
            }

        except Exception as error:
            duration = int(time.time() * 1000) - start_time
            logger.portal_failure('Naukri', error, {'duration': duration})

            return {
                'portal': 'Naukri',
                'success': False,
                'duration': duration,
                'error': str(error),
            }

        finally:
            await close_browser(browser)

    async def _login(self, page, credentials: Dict[str, str]) -> None:
        """Login to Naukri"""
        try:
            await page.goto(PORTALS['naukri']['login_url'], wait_until='networkidle')
            await human_delay(2000)

            # Wait for and enter email/username
            username_selector = "#usernameField"
            await wait_for_selector(page, username_selector)
            await human_type(page, username_selector, credentials['email'])

            # Wait for and enter password
            password_selector = "#passwordField"
            await wait_for_selector(page, password_selector)
            await human_type(page, password_selector, credentials['password'])

            # Click login button
            await safe_click(page, 'button[type="submit"]')

            # Wait for navigation
            await human_delay(3000)

            # Check for profile/dashboard to load (success indicators)
            profile_loaded = await wait_for_selector(
                page,
                '.nI-gNb-drawer__icon, .view-profile-wrapper',
                timeout=15000
            )

            if profile_loaded:
                # Login successful
                logger.info('Login successful - profile indicators found')
                return

            # If success indicators not found, check for login errors
            login_error = await detect_login_errors(page)
            if login_error and login_error['message'].strip():
                raise Exception(f"Login failed: {login_error['message']}")

            # Neither success nor clear error found
            await take_screenshot(page, 'naukri-login-issue')
            raise Exception('Login verification required or CAPTCHA detected')

        except Exception as error:
            await take_screenshot(page, 'naukri-login-error')
            raise Exception(f'Naukri login failed: {str(error)}')

    async def _navigate_to_profile(self, page) -> None:
        """Navigate to profile page"""
        try:
            # Go directly to profile page
            await page.goto('https://www.naukri.com/mnjuser/profile', wait_until='load')
            await human_delay(3000)

            # Wait for profile page elements
            await wait_for_selector(page, '.widgetList, .profileWrapper', timeout=10000)

        except Exception as error:
            await take_screenshot(page, 'naukri-profile-nav-error')
            raise Exception(f'Failed to navigate to profile: {str(error)}')

    async def _read_profile_summary(self, page) -> str:
        """Read current Profile Summary"""
        try:
            # Find and click edit button for Resume Headline/Profile Summary
            edit_selectors = [
                '.resumeHeadline .edit',
                'span.edit.icon:has-text("Profile summary")',
                '#profileSummary .edit',
                'span[title="Edit Profile Summary"]',
            ]

            clicked = False
            for selector in edit_selectors:
                try:
                    await safe_click(page, selector)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                raise Exception('Could not find Profile Summary edit button')

            await human_delay(2000)

            # Wait for edit form/textarea
            await wait_for_selector(page, 'textarea, .input')

            # Find textarea with current content
            textarea_selectors = [
                'textarea[name="summary"]',
                'textarea#profileSummary',
                '.summaryText textarea',
                'textarea',
            ]

            content = None
            for selector in textarea_selectors:
                try:
                    textarea = await page.query_selector(selector)
                    if textarea:
                        content = await textarea.input_value()
                        if content and content.strip():
                            break
                except Exception:
                    continue

            if not content or not content.strip():
                raise Exception('Profile Summary is empty or not found')

            return content.strip()

        except Exception as error:
            await take_screenshot(page, 'naukri-read-summary-error')
            raise Exception(f'Failed to read Profile Summary: {str(error)}')

    async def _update_profile_summary(self, page, new_content: str) -> None:
        """Update Profile Summary with new content"""
        try:
            # Find textarea
            textarea_selectors = [
                'textarea[name="summary"]',
                'textarea#profileSummary',
                '.summaryText textarea',
                'textarea',
            ]

            textarea = None
            for selector in textarea_selectors:
                textarea = await page.query_selector(selector)
                if textarea:
                    break

            if not textarea:
                raise Exception('Profile Summary textarea not found')

            # Clear existing content
            await textarea.click(click_count=3)  # Select all
            await human_delay(500)
            await page.keyboard.press('Backspace')
            await human_delay(500)

            # Type new content
            await textarea.type(new_content, delay=50)
            await human_delay(1000)

            # Click Save button
            save_selectors = [
                'button.btn-dark-ot[type="submit"]',
                'button.btn-dark-ot',
                'button:has-text("Save")',
                'button[type="submit"]',
            ]

            saved = False
            for selector in save_selectors:
                try:
                    # Check if element exists and is visible
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.click()
                        saved = True
                        logger.info(f'Clicked save button with selector: {selector}')
                        break
                except Exception:
                    continue

            if not saved:
                raise Exception('Could not find Save button')

            await human_delay(3000)
            logger.info('Profile Summary update completed')

        except Exception as error:
            await take_screenshot(page, 'naukri-update-summary-error')
            raise Exception(f'Failed to update Profile Summary: {str(error)}')
