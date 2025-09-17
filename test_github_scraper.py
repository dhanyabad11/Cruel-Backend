#!/usr/bin/env python3
"""
Test script for GitHub scraper

This script tests the GitHub scraper functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.scrapers import ScraperRegistry
from app.scrapers.portal_scrapers.github_scraper import GitHubScraper


async def test_github_scraper():
    """Test the GitHub scraper with a public repository."""
    print("Testing GitHub Scraper...")
    
    # Create portal configuration
    portal_config = {
        'type': 'github',
        'name': 'Test GitHub Repository',
        'url': 'https://github.com/octocat/Hello-World',
        'credentials': {},  # No token for testing public API
        'scrape_config': {
            'repo_url': 'https://github.com/octocat/Hello-World',
            'include_closed': False
        }
    }
    
    # Initialize scraper
    scraper = GitHubScraper(portal_config)
    
    # Test credential validation
    print("\n1. Testing credential validation:")
    
    # Valid config (no token needed for public repos)
    is_valid = scraper.validate_credentials()
    print(f"Valid credentials test: {'PASS' if is_valid else 'FAIL'}")
    
    # Test authentication
    print("\n2. Testing authentication:")
    try:
        auth_ok = await scraper.authenticate()
        print(f"Authentication test: {'PASS' if auth_ok else 'FAIL'}")
    except Exception as e:
        print(f"Authentication test failed: {e}")
    
    # Test registry registration
    print("\n3. Testing scraper registry:")
    available_scrapers = ScraperRegistry.get_available_types()
    github_registered = 'github' in available_scrapers
    print(f"GitHub scraper registered: {'PASS' if github_registered else 'FAIL'}")
    
    if github_registered:
        print(f"Available scrapers: {available_scrapers}")
    
    # Test scraping (limited test to avoid API rate limits)
    print("\n4. Testing scraping functionality:")
    try:
        print("Attempting to scrape deadlines...")
        result = await scraper.scrape_deadlines()
        
        print(f"Scraping status: {result.status}")
        print(f"Message: {result.message}")
        print(f"Found {len(result.deadlines)} deadlines.")
        
        if result.errors:
            print(f"Errors: {result.errors}")
        
        if result.deadlines:
            print("\nFirst deadline details:")
            first_deadline = result.deadlines[0]
            print(f"Title: {first_deadline.title}")
            print(f"Due date: {first_deadline.due_date}")
            print(f"Priority: {first_deadline.priority}")
            print(f"Tags: {first_deadline.tags}")
            print(f"Portal URL: {first_deadline.portal_url}")
    
    except Exception as e:
        print(f"Scraping test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nGitHub Scraper test completed!")


if __name__ == "__main__":
    asyncio.run(test_github_scraper())