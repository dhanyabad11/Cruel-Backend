#!/usr/bin/env python3
"""
Test script for Trello scraper

This script tests the Trello scraper functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.scrapers import ScraperRegistry
from app.scrapers.portal_scrapers.trello_scraper import TrelloScraper


async def test_trello_scraper():
    """Test the Trello scraper with a test configuration."""
    print("Testing Trello Scraper...")
    
    # Create portal configuration for testing
    # Note: This uses placeholder credentials - real testing would need actual Trello API keys
    portal_config = {
        'type': 'trello',
        'name': 'Test Trello Workspace',
        'url': 'https://trello.com',
        'credentials': {
            'api_key': 'test-api-key-placeholder',
            'api_token': 'test-api-token-placeholder'
        },
        'scrape_config': {
            'boards': ['board_id_1', 'board_id_2'],
            'board_urls': [
                'https://trello.com/b/abc123/my-board',
                'https://trello.com/b/def456/another-board'
            ],
            'lists': ['To Do', 'In Progress', 'Review'],
            'include_completed': False
        }
    }
    
    # Initialize scraper
    scraper = TrelloScraper(portal_config)
    
    # Test credential validation
    print("\n1. Testing credential validation:")
    
    # Valid config structure
    is_valid = scraper.validate_credentials()
    print(f"Valid credentials structure test: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid config - missing credentials
    invalid_config = {
        'type': 'trello',
        'name': 'Invalid Trello',
        'url': 'https://trello.com',
        'credentials': {},
        'scrape_config': {}
    }
    invalid_scraper = TrelloScraper(invalid_config)
    is_invalid = not invalid_scraper.validate_credentials()
    print(f"Invalid credentials test: {'PASS' if is_invalid else 'FAIL'}")
    
    # Test invalid config - no boards specified
    no_boards_config = {
        'type': 'trello',
        'name': 'No Boards Trello',
        'url': 'https://trello.com',
        'credentials': {
            'api_key': 'test-key',
            'api_token': 'test-token'
        },
        'scrape_config': {}
    }
    no_boards_scraper = TrelloScraper(no_boards_config)
    no_boards_invalid = not no_boards_scraper.validate_credentials()
    print(f"No boards config test: {'PASS' if no_boards_invalid else 'FAIL'}")
    
    # Test URL validation
    print("\n2. Testing URL validation:")
    
    test_urls = [
        ('https://trello.com/b/abc123/my-board', True),
        ('https://www.trello.com/b/def456/another-board', True),
        ('https://trello.com/c/xyz789/my-card', True),
        ('https://invalid-site.com/b/abc123/board', False),
        ('https://trello.com/invalid/path', False),
        ('invalid-url', False),
        ('', False)
    ]
    
    for url, expected in test_urls:
        result = scraper._is_valid_trello_url(url)
        status = 'PASS' if result == expected else 'FAIL'
        print(f"URL validation for {url}: {status}")
    
    # Test board ID extraction
    print("\n3. Testing board ID extraction:")
    
    board_url_tests = [
        ('https://trello.com/b/abc123/my-board', 'abc123'),
        ('https://www.trello.com/b/def456/another-board-name', 'def456'),
        ('https://trello.com/c/xyz789/card-name', None),
        ('invalid-url', None)
    ]
    
    for url, expected_id in board_url_tests:
        result = scraper._extract_board_id_from_url(url)
        status = 'PASS' if result == expected_id else 'FAIL'
        print(f"Board ID extraction for {url}: {result} - {status}")
    
    # Test registry registration
    print("\n4. Testing scraper registry:")
    available_scrapers = ScraperRegistry.get_available_types()
    trello_registered = 'trello' in available_scrapers
    print(f"Trello scraper registered: {'PASS' if trello_registered else 'FAIL'}")
    
    if trello_registered:
        print(f"Available scrapers: {available_scrapers}")
    
    # Test priority mapping
    print("\n5. Testing priority mapping:")
    
    priority_tests = [
        ([{'name': 'Urgent', 'color': 'red'}], 'high'),
        ([{'name': 'Critical Issue', 'color': 'blue'}], 'high'),
        ([{'name': '', 'color': 'red'}], 'high'),
        ([{'name': 'Low Priority', 'color': 'green'}], 'low'),
        ([{'name': 'Nice to Have', 'color': 'blue'}], 'low'),
        ([{'name': '', 'color': 'green'}], 'low'),
        ([{'name': 'Normal Task', 'color': 'blue'}], 'medium'),
        ([], 'medium')
    ]
    
    for labels, expected in priority_tests:
        result = scraper._determine_priority_from_labels(labels)
        status = 'PASS' if result == expected else 'FAIL'
        label_desc = labels[0].get('name', f"color:{labels[0].get('color')}") if labels else 'No labels'
        print(f"Priority mapping for {label_desc}: {result} - {status}")
    
    # Test time estimate extraction
    print("\n6. Testing time estimate extraction:")
    
    time_tests = [
        ('This task will take 5 hours to complete', 5),
        ('Estimate: 8h', 8),
        ('Time needed: 12 hours', 12),
        ('Effort: 3hrs', 3),
        ('Should take about 2h', 2),
        ('No time estimate here', None),
        ('', None)
    ]
    
    for text, expected in time_tests:
        result = scraper._extract_time_estimate_from_text(text)
        status = 'PASS' if result == expected else 'FAIL'
        print(f"Time estimate for '{text[:30]}...': {result} - {status}")
    
    # Test text truncation
    print("\n7. Testing text utilities:")
    
    long_text = "A" * 1000
    truncated = scraper._truncate_text(long_text, 500)
    truncation_test = len(truncated) == 503 and truncated.endswith('...')  # 500 + '...'
    print(f"Text truncation test: {'PASS' if truncation_test else 'FAIL'}")
    
    empty_truncated = scraper._truncate_text('', 100)
    empty_test = empty_truncated == ''
    print(f"Empty text truncation test: {'PASS' if empty_test else 'FAIL'}")
    
    # Test authentication (will fail with placeholder credentials)
    print("\n8. Testing authentication:")
    try:
        auth_result = await scraper.authenticate()
        print(f"Authentication test: {'PASS' if auth_result else 'EXPECTED_FAIL (placeholder credentials)'}")
    except Exception as e:
        print(f"Authentication test: EXPECTED_FAIL (placeholder credentials) - {e}")
    
    # Test scraping functionality (will fail with placeholder credentials)
    print("\n9. Testing scraping functionality:")
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
    
    print("\nTrello Scraper test completed!")
    print("\nNote: Authentication and scraping tests fail with placeholder credentials.")
    print("For real testing, provide valid Trello API key and token.")
    print("Get your API credentials from: https://trello.com/app-key")


if __name__ == "__main__":
    asyncio.run(test_trello_scraper())