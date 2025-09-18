"""
Portal Scrapers Package

This package contains specific scraper implementations for various portals
like GitHub, Jira, Trello, etc.
"""

from .github_scraper import GitHubScraper
from .jira_scraper import JiraScraper

__all__ = ['GitHubScraper', 'JiraScraper']