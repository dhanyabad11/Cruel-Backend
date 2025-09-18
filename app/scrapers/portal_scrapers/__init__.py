"""
Portal Scrapers Package

This package contains specific scraper implementations for various portals
like GitHub, Jira, Trello, etc.
"""

from .github_scraper import GitHubScraper
from .jira_scraper import JiraScraper
from .trello_scraper import TrelloScraper

__all__ = ['GitHubScraper', 'JiraScraper', 'TrelloScraper']