"""
Portal Scrapers Package

This package contains specific scraper implementations for various portals
like GitHub, Jira, Trello, etc.
"""

from .github_scraper import GitHubScraper

__all__ = ['GitHubScraper']