"""
LinkedIn Profile Automation
Automates login and "About" section update on LinkedIn
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

logger = Logger('LinkedIn')


class LinkedInAutomation:
    """LinkedIn profile automation handler"""

    def __init__(self):
        self.bedrock = BedrockService()

    async def execute(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute LinkedIn profile update

        Args:
            credentials: LinkedIn credentials {email, password}

        Returns:
            Execution result dictionary
        """
        start_time = int(time.time() * 1000)
        browser = None

        try:
            logger.portal_start('LinkedIn')

            # Launch browser
            browser, context, page = await launch_browser()

            # Login
            await self._login(page, credentials)
            logger.info('LinkedIn login successful')

            # Navigate to profile edit
            await self._navigate_to_profile(page)
            logger.info('Navigated to profile page')

            # Read current "About" section
            current_about = await self._read_about_section(page)
            logger.info('Read current About section', {'length': len(current_about)})

            # Mutate content using AI
            new_about = self.bedrock.mutate_content(current_about, 'LinkedIn About/Summary')

            # Validate mutation
            if not self.bedrock.validate_mutation(current_about, new_about):
                raise Exception('Content mutation validation failed')

            # Update About section
            await self._update_about_section(page, new_about)
            logger.info('Updated About section successfully')

            duration = int(time.time() * 1000) - start_time
            logger.portal_success('LinkedIn', {'duration': duration})

            return {
                'portal': 'LinkedIn',
                'success': True,
                'duration': duration,
                'details': {'content_length': len(new_about)},
            }

        except Exception as error:
            duration = int(time.time() * 1000) - start_time
            logger.portal_failure('LinkedIn', error, {'duration': duration})

            return {
                'portal': 'LinkedIn',
                'success': False,
                'duration': duration,
                'error': str(error),
            }

        finally:
            await close_browser(browser)

    async def _login(self, page, credentials: Dict[str, str]) -> None:
        """Login to LinkedIn"""
        try:
            await page.goto(PORTALS['linkedin']['login_url'], wait_until='load')
            await human_delay(2000)

            # Wait for and enter email
            await wait_for_selector(page, '#username')
            await human_type(page, '#username', credentials['email'])

            # Wait for and enter password
            await wait_for_selector(page, '#password')
            await human_type(page, '#password', credentials['password'])

            # Click sign in
            await safe_click(page, 'button[type="submit"]')

            # Wait for navigation
            await human_delay(5000)

            # Check for feed or profile to load (success indicators first)
            feed_loaded = await wait_for_selector(
                page,
                '[data-test-id="feed-container"], nav.global-nav, .feed-shared-update-v2',
                timeout=15000
            )

            if feed_loaded:
                # Login successful
                logger.info('Login successful - feed indicators found')
                return

            # If success indicators not found, check for login errors
            login_error = await detect_login_errors(page)
            if login_error and login_error['message'].strip():
                raise Exception(f"Login failed: {login_error['message']}")

            # Neither success nor clear error found
            await take_screenshot(page, 'linkedin-login-issue')
            raise Exception('Login verification required or CAPTCHA detected')

        except Exception as error:
            await take_screenshot(page, 'linkedin-login-error')
            raise Exception(f'LinkedIn login failed: {str(error)}')

    async def _navigate_to_profile(self, page) -> None:
        """Navigate to profile edit page"""
        try:
            # Click on "Me" menu
            me_selectors = [
                '.global-nav__me',
                'button[data-test-nav-item="me"]',
                'button[aria-label*="Me"]',
            ]

            me_clicked = False
            for selector in me_selectors:
                try:
                    await safe_click(page, selector)
                    me_clicked = True
                    logger.info(f'Clicked Me menu with selector: {selector}')
                    break
                except:
                    continue

            if not me_clicked:
                raise Exception('Could not find Me menu button')

            await human_delay(2000)

            # Click "View Profile"
            view_profile_selectors = [
                'a[data-control-name="view_profile"]',
                'a[href*="/in/"]',
                'div[data-control-name="identity_profile_card"] a',
            ]

            profile_clicked = False
            for selector in view_profile_selectors:
                try:
                    await safe_click(page, selector)
                    profile_clicked = True
                    logger.info(f'Clicked View Profile with selector: {selector}')
                    break
                except:
                    continue

            if not profile_clicked:
                raise Exception('Could not find View Profile link')

            await human_delay(3000)

            # Wait for profile page to load
            await wait_for_selector(page, '.pv-text-details__left-panel, .ph5', timeout=15000)

        except Exception as error:
            await take_screenshot(page, 'linkedin-profile-nav-error')
            raise Exception(f'Failed to navigate to profile: {str(error)}')

    async def _read_about_section(self, page) -> str:
        """Read current About section"""
        try:
            # Click "Edit intro" button (LinkedIn combined About into intro editing)
            edit_selectors = [
                'button[aria-label="Edit intro"]',
                'button[aria-label*="Edit intro"]',
                'button:has-text("Edit intro")',
            ]

            edit_clicked = False
            for selector in edit_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        await elem.click()
                        edit_clicked = True
                        logger.info(f'Clicked edit button with selector: {selector}')
                        break
                except:
                    continue

            if not edit_clicked:
                raise Exception('Could not find Edit intro button')

            await human_delay(3000)

            # Wait for edit modal
            await wait_for_selector(page, 'div[role="dialog"]', timeout=10000)

            # Find the textarea with current content (headline/about)
            textarea_selectors = [
                'div[role="dialog"] textarea',
                'textarea[name="summary"]',
                '#about-edit-form textarea',
            ]

            textarea = None
            for selector in textarea_selectors:
                textarea = await page.query_selector(selector)
                if textarea:
                    break

            if not textarea:
                raise Exception('About section textarea not found')

            content = await textarea.input_value()

            if not content or not content.strip():
                raise Exception('About section is empty')

            return content.strip()

        except Exception as error:
            await take_screenshot(page, 'linkedin-read-about-error')
            raise Exception(f'Failed to read About section: {str(error)}')

    async def _update_about_section(self, page, new_content: str) -> None:
        """Update About section with new content"""
        try:
            # Find textarea
            textarea_selectors = [
                'div[role="dialog"] textarea',
                'textarea[name="summary"]',
                '#about-edit-form textarea',
            ]

            textarea = None
            for selector in textarea_selectors:
                textarea = await page.query_selector(selector)
                if textarea:
                    break

            if not textarea:
                raise Exception('About section textarea not found')

            # Clear and fill with new content (faster than character-by-character typing)
            await textarea.fill('')  # Clear
            await human_delay(500)
            await textarea.fill(new_content)  # Fill all at once
            await human_delay(1000)

            # Click Save button
            save_selectors = [
                'button[aria-label="Save"]',
                'button:has-text("Save")',
                'div[role="dialog"] button[type="submit"]',
            ]

            save_clicked = False
            for selector in save_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        await elem.click()
                        save_clicked = True
                        logger.info(f'Clicked save button with selector: {selector}')
                        break
                except:
                    continue

            if not save_clicked:
                raise Exception('Could not find Save button')

            await human_delay(3000)

            # Verify save was successful
            modal_closed = await page.query_selector('div[role="dialog"]') is None
            if not modal_closed:
                logger.warn('Save modal did not close immediately, giving it more time')
                await human_delay(2000)
                modal_closed = await page.query_selector('div[role="dialog"]') is None

            logger.info(f'Profile update completed, modal closed: {modal_closed}')

        except Exception as error:
            await take_screenshot(page, 'linkedin-update-about-error')
            raise Exception(f'Failed to update About section: {str(error)}')
