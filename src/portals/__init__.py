"""Portal automation modules"""

from .linkedin import LinkedInAutomation
from .naukri import NaukriAutomation
from .indeed import IndeedAutomation

# Singleton instances
linkedin_automation = LinkedInAutomation()
naukri_automation = NaukriAutomation()
indeed_automation = IndeedAutomation()

__all__ = [
    'LinkedInAutomation',
    'NaukriAutomation',
    'IndeedAutomation',
    'linkedin_automation',
    'naukri_automation',
    'indeed_automation',
]
