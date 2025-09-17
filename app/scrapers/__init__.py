from .base_scraper import BaseScraper, ScrapedDeadline, ScrapingResult, ScrapingStatus
from .scraper_registry import ScraperRegistry, register_scraper, scrape_portal, scrape_user_portals
from .utils import ScrapingUtils, APIHelper

# Import portal scrapers here as they're created
from .portal_scrapers.github_scraper import GitHubScraper
# from .portal_scrapers.jira_scraper import JiraScraper
# from .portal_scrapers.trello_scraper import TrelloScraper

__all__ = [
    "BaseScraper",
    "ScrapedDeadline", 
    "ScrapingResult",
    "ScrapingStatus",
    "ScraperRegistry",
    "register_scraper",
    "scrape_portal",
    "scrape_user_portals",
    "ScrapingUtils",
    "APIHelper",
]

def get_available_scrapers():
    """Get list of available scraper types"""
    return ScraperRegistry.get_available_types()

def validate_scraper_config(portal_type: str, config: dict) -> bool:
    """Validate scraper configuration for a portal type"""
    scraper_class = ScraperRegistry.get_scraper(portal_type)
    if not scraper_class:
        return False
    
    # Create a temporary instance to validate
    try:
        temp_scraper = scraper_class(config)
        return temp_scraper.validate_credentials()
    except Exception:
        return False