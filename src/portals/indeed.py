"""
Indeed Profile Automation
Automates login and "Skills" section update on Indeed
NOTE: Indeed may require email OTP verification
"""

import time
from typing import Dict, Any, Optional

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

logger = Logger('Indeed')


class IndeedAutomation:
    """Indeed profile automation handler"""

    def __init__(self):
        self.bedrock = BedrockService()

    async def execute(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute Indeed profile update

        Args:
            credentials: Indeed credentials {email, password}

        Returns:
            Execution result dictionary
        """
        start_time = int(time.time() * 1000)
        browser = None

        try:
            logger.portal_start('Indeed')

            # Launch browser
            browser, context, page = await launch_browser()

            # Login (may require OTP)
            await self._login(page, credentials)
            logger.info('Indeed login successful')

            # Navigate to profile/resume page
            await self._navigate_to_profile(page)
            logger.info('Navigated to profile page')

            # Read current Skills section
            current_skills = await self._read_skills(page)
            logger.info('Read current Skills', {'length': len(current_skills)})

            # Mutate content using AI
            new_skills = self.bedrock.mutate_content(current_skills, 'Indeed Skills')

            # Validate mutation
            if not self.bedrock.validate_mutation(current_skills, new_skills):
                raise Exception('Content mutation validation failed')

            # Update Skills
            await self._update_skills(page, new_skills)
            logger.info('Updated Skills successfully')

            duration = int(time.time() * 1000) - start_time
            logger.portal_success('Indeed', {'duration': duration})

            return {
                'portal': 'Indeed',
                'success': True,
                'duration': duration,
                'details': {'content_length': len(new_skills)},
            }

        except Exception as error:
            duration = int(time.time() * 1000) - start_time
            logger.portal_failure('Indeed', error, {'duration': duration})

            return {
                'portal': 'Indeed',
                'success': False,
                'duration': duration,
                'error': str(error),
            }

        finally:
            await close_browser(browser)

    async def _login(self, page, credentials: Dict[str, str]) -> None:
        """Login to Indeed"""
        try:
            await page.goto(PORTALS['indeed']['login_url'], wait_until='networkidle')
            await human_delay(2000)

            # Enter email
            await human_type(page, '#ifl-InputFormField-3, input[type="email"], #login-email-input', credentials['email'])

            # Check if there's a "Continue" button (multi-step login)
            continue_button = await page.query_selector('button:has-text("Continue")')
            if continue_button:
                await continue_button.click()
                await human_delay(2000)

            # Enter password
            await human_type(page, '#ifl-InputFormField-7, input[type="password"], #login-password-input', credentials['password'])

            # Click login/sign in button
            await safe_click(page, 'button[type="submit"], button:has-text("Sign in")')

            # Wait for navigation or OTP prompt
            await human_delay(5000)

            # Check for OTP requirement
            otp_required = await self._check_otp_required(page)
            if otp_required:
                logger.warn('OTP verification required for Indeed login')
                raise Exception('OTP verification required - cannot proceed automatically')

            # Check for login errors
            login_error = await detect_login_errors(page)
            if login_error:
                raise Exception(f"Login failed: {login_error['message']}")

            # Wait for dashboard/profile to load
            profile_loaded = await wait_for_selector(
                page,
                '[data-testid="profile-card"], .profile-link',
                timeout=15000
            )

            if not profile_loaded:
                await take_screenshot(page, 'indeed-login-issue')
                raise Exception('Login verification required or CAPTCHA detected')

        except Exception as error:
            await take_screenshot(page, 'indeed-login-error')
            raise Exception(f'Indeed login failed: {str(error)}')

    async def _check_otp_required(self, page) -> bool:
        """Check if OTP is required"""
        otp_selectors = [
            'input[type="text"][placeholder*="code"]',
            'input[name="otp"]',
            'input[aria-label*="verification"]',
        ]

        for selector in otp_selectors:
            otp_field = await page.query_selector(selector)
            if otp_field:
                return True

        return False

    async def _navigate_to_profile(self, page) -> None:
        """Navigate to profile/resume page"""
        try:
            # Go directly to profile page
            await page.goto('https://profile.indeed.com/', wait_until='networkidle')
            await human_delay(2000)

            # Wait for profile page elements
            await wait_for_selector(page, '[data-testid="profile-card"], .profile-section')

        except Exception as error:
            await take_screenshot(page, 'indeed-profile-nav-error')
            raise Exception(f'Failed to navigate to profile: {str(error)}')

    async def _read_skills(self, page) -> str:
        """Read current Skills section"""
        try:
            # Find Skills section and click edit
            edit_selectors = [
                '[data-testid="skills-edit-button"]',
                'button[aria-label*="Edit skills"]',
                '.skills-section .edit-button',
                'button:has-text("Edit skills")',
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
                raise Exception('Could not find Skills edit button')

            await human_delay(2000)

            # Wait for edit form
            await wait_for_selector(page, 'textarea, input[type="text"]')

            # Find textarea or input with current skills
            skills_selectors = [
                'textarea[name="skills"]',
                'textarea[aria-label*="Skills"]',
                'input[name="skills"]',
                'textarea',
            ]

            content = None
            for selector in skills_selectors:
                try:
                    field = await page.query_selector(selector)
                    if field:
                        content = await field.input_value()
                        if content and content.strip():
                            break
                except Exception:
                    continue

            if not content or not content.strip():
                raise Exception('Skills section is empty or not found')

            return content.strip()

        except Exception as error:
            await take_screenshot(page, 'indeed-read-skills-error')
            raise Exception(f'Failed to read Skills: {str(error)}')

    async def _update_skills(self, page, new_skills: str) -> None:
        """Update Skills with new content"""
        try:
            # Find skills input field
            skills_selectors = [
                'textarea[name="skills"]',
                'textarea[aria-label*="Skills"]',
                'input[name="skills"]',
                'textarea',
            ]

            field = None
            for selector in skills_selectors:
                field = await page.query_selector(selector)
                if field:
                    break

            if not field:
                raise Exception('Skills input field not found')

            # Clear existing content
            await field.click(click_count=3)  # Select all
            await human_delay(500)
            await page.keyboard.press('Backspace')
            await human_delay(500)

            # Type new content
            await field.type(new_skills, delay=50)
            await human_delay(1000)

            # Click Save button
            save_selectors = [
                'button[type="submit"]',
                'button:has-text("Save")',
                'button[aria-label*="Save"]',
                '.save-button',
            ]

            saved = False
            for selector in save_selectors:
                try:
                    await safe_click(page, selector)
                    saved = True
                    break
                except Exception:
                    continue

            if not saved:
                raise Exception('Could not find Save button')

            await human_delay(3000)
            logger.info('Skills update completed')

        except Exception as error:
            await take_screenshot(page, 'indeed-update-skills-error')
            raise Exception(f'Failed to update Skills: {str(error)}')
