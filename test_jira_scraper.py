#!/usr/bin/env python3
"""
Test script for Jira scraper

This script tests the Jira scraper functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.scrapers import ScraperRegistry
from app.scrapers.portal_scrapers.jira_scraper import JiraScraper


async def test_jira_scraper():
    """Test the Jira scraper with a test configuration."""
    print("Testing Jira Scraper...")
    
    # Create portal configuration for testing
    # Note: This uses placeholder credentials - real testing would need actual Jira instance
    portal_config = {
        'type': 'jira',
        'name': 'Test Jira Instance',
        'url': 'https://example.atlassian.net',
        'credentials': {
            'username': 'test@example.com',
            'api_token': 'test-token-placeholder'
        },
        'scrape_config': {
            'projects': ['TEST', 'DEMO'],
            'max_results': 50,
            'statuses': ['To Do', 'In Progress', 'In Review']
        }
    }
    
    # Initialize scraper
    scraper = JiraScraper(portal_config)
    
    # Test credential validation
    print("\n1. Testing credential validation:")
    
    # Valid config structure
    is_valid = scraper.validate_credentials()
    print(f"Valid credentials structure test: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid config
    invalid_config = {
        'type': 'jira',
        'name': 'Invalid Jira',
        'url': 'invalid-url',
        'credentials': {},
        'scrape_config': {}
    }
    invalid_scraper = JiraScraper(invalid_config)
    is_invalid = not invalid_scraper.validate_credentials()
    print(f"Invalid credentials test: {'PASS' if is_invalid else 'FAIL'}")
    
    # Test URL validation
    print("\n2. Testing URL validation:")
    
    # Test various Jira URL formats
    test_urls = [
        ('https://company.atlassian.net', True),
        ('https://jira.company.com', True),
        ('http://localhost:8080', True),
        ('invalid-url', False),
        ('ftp://example.com', False),
        ('', False),
        ('not-a-url', False)
    ]
    
    for url, expected in test_urls:
        result = scraper._is_valid_jira_url(url)
        status = 'PASS' if result == expected else 'FAIL'
        print(f"URL validation for {url}: {status}")
    
    # Test registry registration
    print("\n3. Testing scraper registry:")
    available_scrapers = ScraperRegistry.get_available_types()
    jira_registered = 'jira' in available_scrapers
    print(f"Jira scraper registered: {'PASS' if jira_registered else 'FAIL'}")
    
    if jira_registered:
        print(f"Available scrapers: {available_scrapers}")
    
    # Test authentication (will fail with placeholder credentials)
    print("\n4. Testing authentication:")
    try:
        auth_result = await scraper.authenticate()
        print(f"Authentication test: {'PASS' if auth_result else 'EXPECTED_FAIL (placeholder credentials)'}")
    except Exception as e:
        print(f"Authentication test: EXPECTED_FAIL (placeholder credentials) - {e}")
    
    # Test API base URL generation
    print("\n5. Testing API URL generation:")
    
    test_base_urls = [
        ('https://company.atlassian.net', 'https://company.atlassian.net/rest/api/2'),
        ('https://jira.company.com/', 'https://jira.company.com/rest/api/2'),
        ('https://jira.company.com/rest/api/2', 'https://jira.company.com/rest/api/2')
    ]
    
    for base_url, expected_api_url in test_base_urls:
        test_config = portal_config.copy()
        test_config['url'] = base_url
        test_scraper = JiraScraper(test_config)
        api_url = test_scraper._get_api_base()
        status = 'PASS' if api_url == expected_api_url else 'FAIL'
        print(f"API URL for {base_url}: {api_url} - {status}")
    
    # Test priority mapping
    print("\n6. Testing priority mapping:")
    
    priority_tests = [
        ({'name': 'Highest'}, 'high'),
        ({'name': 'Critical'}, 'high'),
        ({'name': 'Blocker'}, 'high'),
        ({'name': 'Medium'}, 'medium'),
        ({'name': 'Low'}, 'medium'),
        ({'name': 'Lowest'}, 'low'),
        ({'name': 'Trivial'}, 'low'),
        ({}, 'medium')
    ]
    
    for priority_obj, expected in priority_tests:
        result = scraper._determine_priority_from_jira_priority(priority_obj)
        status = 'PASS' if result == expected else 'FAIL'
        priority_name = priority_obj.get('name', 'None')
        print(f"Priority mapping for {priority_name}: {result} - {status}")
    
    # Test text truncation
    print("\n7. Testing text utilities:")
    
    long_text = "A" * 1000
    truncated = scraper._truncate_text(long_text, 500)
    truncation_test = len(truncated) == 503 and truncated.endswith('...')  # 500 + '...'
    print(f"Text truncation test: {'PASS' if truncation_test else 'FAIL'}")
    
    empty_truncated = scraper._truncate_text('', 100)
    empty_test = empty_truncated == ''
    print(f"Empty text truncation test: {'PASS' if empty_test else 'FAIL'}")
    
    # Test scraping functionality (will fail with placeholder credentials)
    print("\n8. Testing scraping functionality:")
    try:
        print("Attempting to scrape deadlines...")
        result = await scraper.scrape_deadlines()
        
        print(f"Scraping status: {result.status}")
        print(f"Message: {result.message}")
        print(f"Found {len(result.deadlines)} deadlines.")
        
        if result.errors:
            print(f"Expected errors (due to placeholder credentials): {result.errors}")
        
    except Exception as e:
        print(f"Scraping test: EXPECTED_FAIL (placeholder credentials) - {e}")
    
    print("\nJira Scraper test completed!")
    print("\nNote: Authentication and scraping tests fail with placeholder credentials.")
    print("For real testing, provide valid Jira instance URL and credentials.")


if __name__ == "__main__":
    asyncio.run(test_jira_scraper())