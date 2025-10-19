#!/usr/bin/env python3
"""
Portal Scraping Test Script

This script tests the portal scraping functionality by:
1. Creating a test portal (GitHub)
2. Running a sync to scrape deadlines
3. Displaying the results

Usage:
    python test_portal_scraping.py --token YOUR_GITHUB_TOKEN --repo owner/repo
"""

import asyncio
import sys
import argparse
from datetime import datetime
from app.scrapers import ScraperRegistry, scrape_portal
from app.scrapers.base_scraper import ScrapingStatus


class MockPortal:
    """Mock portal object for testing"""
    def __init__(self, portal_type, name, url, credentials, config):
        self.id = 1
        self.user_id = "test-user"
        self.portal_type = portal_type
        self.name = name
        self.url = url
        self.credentials = credentials
        self.config = config
        self.is_active = True
    
    def __getitem__(self, key):
        """Make object subscriptable like a dict"""
        return getattr(self, key)
    
    def get(self, key, default=None):
        """Dict-like get method"""
        return getattr(self, key, default)


async def test_github_scraper(github_token: str, repo: str):
    """Test GitHub scraper"""
    print("=" * 60)
    print("🔍 TESTING GITHUB PORTAL SCRAPER")
    print("=" * 60)
    
    # Create mock portal
    portal = MockPortal(
        portal_type="github",
        name="Test GitHub Portal",
        url="https://github.com",
        credentials={"token": github_token},
        config={
            "repos": [repo],
            "include_issues": True,
            "include_prs": True,
            "include_assigned_only": False
        }
    )
    
    print(f"\n📋 Portal Configuration:")
    print(f"   Type: {portal.portal_type}")
    print(f"   Name: {portal.name}")
    print(f"   Repo: {repo}")
    print(f"   Token: {github_token[:10]}..." if github_token else "   Token: None")
    
    # Run scraper
    print(f"\n🔄 Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    try:
        result = await scrape_portal(portal)
        
        print(f"\n✅ Scrape Complete!")
        print(f"   Status: {result.status.value}")
        print(f"   Deadlines Found: {len(result.deadlines)}")
        
        if result.errors:
            print(f"\n⚠️  Errors/Warnings:")
            for error in result.errors:
                print(f"   - {error}")
        
        if result.deadlines:
            print(f"\n📅 Scraped Deadlines:")
            print("-" * 60)
            for i, deadline in enumerate(result.deadlines, 1):
                print(f"\n{i}. {deadline.title}")
                print(f"   Due: {deadline.due_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Priority: {deadline.priority}")
                if deadline.description:
                    desc = deadline.description[:100] + "..." if len(deadline.description) > 100 else deadline.description
                    print(f"   Description: {desc}")
                if deadline.tags:
                    print(f"   Tags: {', '.join(deadline.tags)}")
                if deadline.portal_url:
                    print(f"   URL: {deadline.portal_url}")
                if deadline.estimated_hours:
                    print(f"   Estimated: {deadline.estimated_hours}h")
        else:
            print("\n📭 No deadlines found.")
            print("   This could mean:")
            print("   - No issues/PRs with due dates in the repo")
            print("   - Issues don't have due date labels/milestones")
            print("   - Try adding 'due:', 'deadline:' or 'target:' in issue descriptions")
        
        return result.status == ScrapingStatus.SUCCESS
        
    except Exception as e:
        print(f"\n❌ Scraping Failed!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_scraper_registry():
    """Test scraper registry"""
    print("\n" + "=" * 60)
    print("📚 AVAILABLE SCRAPERS")
    print("=" * 60)
    
    available = ScraperRegistry.get_available_types()
    print(f"\n✅ {len(available)} scrapers registered:")
    for scraper_type in sorted(available):
        scraper_class = ScraperRegistry.get_scraper(scraper_type)
        print(f"   - {scraper_type.upper()}: {scraper_class.__name__}")
    
    return True


async def main():
    parser = argparse.ArgumentParser(description='Test portal scraping functionality')
    parser.add_argument('--token', help='GitHub personal access token', required=False)
    parser.add_argument('--repo', help='GitHub repository (owner/repo)', default='torvalds/linux')
    parser.add_argument('--test-registry', action='store_true', help='Test scraper registry only')
    
    args = parser.parse_args()
    
    print("\n🚀 Portal Scraping Test Suite")
    print("=" * 60)
    
    # Test registry
    await test_scraper_registry()
    
    if args.test_registry:
        return
    
    # Test GitHub scraper
    if not args.token:
        print("\n⚠️  No GitHub token provided!")
        print("   To test scraping with authentication:")
        print("   python test_portal_scraping.py --token YOUR_TOKEN --repo owner/repo")
        print("\n   Get a token at: https://github.com/settings/tokens")
        print("   Required scopes: repo, read:user")
        print("\n   Testing with public API (limited rate limits)...")
        github_token = ""
    else:
        github_token = args.token
    
    success = await test_github_scraper(github_token, args.repo)
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Portal scraping is working!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
