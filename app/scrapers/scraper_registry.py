from typing import Dict, Type, List, Optional
from app.scrapers.base_scraper import BaseScraper, ScrapingResult
from app.models.portal import Portal
from app.models.user import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class ScraperRegistry:
    """Registry for managing portal scrapers"""
    
    _scrapers: Dict[str, Type[BaseScraper]] = {}
    
    @classmethod
    def register(cls, portal_type: str, scraper_class: Type[BaseScraper]):
        """Register a scraper for a portal type"""
        cls._scrapers[portal_type.lower()] = scraper_class
        logger.info(f"Registered scraper for {portal_type}: {scraper_class.__name__}")
    
    @classmethod
    def get_scraper(cls, portal_type: str) -> Optional[Type[BaseScraper]]:
        """Get scraper class for a portal type"""
        return cls._scrapers.get(portal_type.lower())
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available portal types"""
        return list(cls._scrapers.keys())
    
    @classmethod
    def create_scraper(cls, portal: Portal) -> Optional[BaseScraper]:
        """Create a scraper instance for a portal"""
        scraper_class = cls.get_scraper(portal.type)
        if not scraper_class:
            logger.error(f"No scraper found for portal type: {portal.type}")
            return None
        
        # Prepare portal configuration
        portal_config = {
            "type": portal.type,
            "name": portal.name,
            "url": portal.url,
            "credentials": portal.credentials or {},
            "scrape_config": portal.scrape_config or {},
            "portal_id": portal.id,
        }
        
        try:
            scraper = scraper_class(portal_config)
            logger.info(f"Created scraper for {portal.name} ({portal.type})")
            return scraper
        except Exception as e:
            logger.error(f"Failed to create scraper for {portal.name}: {str(e)}")
            return None

# Decorator for auto-registering scrapers
def register_scraper(portal_type: str):
    """Decorator to automatically register scrapers"""
    def decorator(scraper_class: Type[BaseScraper]):
        ScraperRegistry.register(portal_type, scraper_class)
        return scraper_class
    return decorator

# Scraper factory functions
async def scrape_portal(portal: Portal) -> ScrapingResult:
    """Scrape a single portal and return results"""
    scraper = ScraperRegistry.create_scraper(portal)
    if not scraper:
        return ScrapingResult(
            status="error",
            deadlines=[],
            message=f"No scraper available for portal type: {portal.type}",
            errors=[f"Unsupported portal type: {portal.type}"]
        )
    
    try:
        # Validate credentials
        if not scraper.validate_credentials():
            return scraper.create_error_result(
                "Invalid or missing credentials",
                ["Portal credentials are invalid or incomplete"]
            )
        
        # Authenticate
        if not await scraper.authenticate():
            return scraper.create_error_result(
                "Authentication failed",
                ["Failed to authenticate with portal"]
            )
        
        # Scrape deadlines
        scraper.log_scraping_start()
        result = await scraper.scrape_deadlines()
        scraper.log_scraping_complete(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error scraping portal {portal.name}: {str(e)}")
        return scraper.create_error_result(
            f"Scraping failed: {str(e)}",
            [str(e)]
        )

async def scrape_user_portals(user: User, db: Session) -> Dict[int, ScrapingResult]:
    """Scrape all active portals for a user"""
    results = {}
    
    # Get all active portals for the user
    portals = db.query(Portal).filter(
        Portal.user_id == user.id,
        Portal.is_active == True
    ).all()
    
    logger.info(f"Scraping {len(portals)} portals for user {user.email}")
    
    for portal in portals:
        try:
            result = await scrape_portal(portal)
            results[portal.id] = result
            
            # Update portal sync status
            portal.sync_status = result.status.value
            if result.status.value == "error" and result.errors:
                portal.last_error = "; ".join(result.errors)
            else:
                portal.last_error = None
                
            portal.sync_count += 1
            
        except Exception as e:
            logger.error(f"Failed to scrape portal {portal.name}: {str(e)}")
            results[portal.id] = ScrapingResult(
                status="error",
                deadlines=[],
                message=f"Failed to scrape portal: {str(e)}",
                errors=[str(e)]
            )
    
    db.commit()
    return results