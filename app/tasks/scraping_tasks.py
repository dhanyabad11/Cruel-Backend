"""
Scraping Tasks

Background tasks for automated portal scraping and deadline synchronization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.models import User, Portal, Deadline
from app.scrapers.scraper_registry import ScraperRegistry
from app.scrapers.base_scraper import ScrapedDeadline

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for tasks"""
    return SessionLocal()


@shared_task(bind=True, name='app.tasks.scraping_tasks.scrape_portal')
def scrape_portal(self, portal_id: int):
    """
    Scrape a specific portal for deadlines.
    
    Args:
        portal_id: ID of the portal to scrape
        
    Returns:
        Dict with scraping results
    """
    db = get_db_session()
    try:
        # Get portal
        portal = db.query(Portal).filter(Portal.id == portal_id).first()
        if not portal:
            logger.error(f"Portal {portal_id} not found")
            return {"success": False, "error": "Portal not found"}
        
        # Get user
        user = db.query(User).filter(User.id == portal.user_id).first()
        if not user:
            logger.error(f"User {portal.user_id} not found")
            return {"success": False, "error": "User not found"}
        
        # Get scraper
        scraper = ScraperRegistry.create_scraper(portal)
        if not scraper:
            logger.error(f"No scraper found for {portal.type}")
            return {"success": False, "error": f"No scraper for {portal.type}"}
        
        # Run scraping
        logger.info(f"Starting scrape for portal {portal_id} ({portal.type})")
        
        try:
            # Run async scraping in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(scraper.scrape())
            
            loop.close()
            
            if result.status.value == "success":
                scraped_deadlines = result.deadlines
            else:
                logger.error(f"Scraping failed for portal {portal_id}: {result.message}")
                return {"success": False, "error": result.message}
            
        except Exception as e:
            logger.error(f"Scraping failed for portal {portal_id}: {e}")
            return {"success": False, "error": str(e)}
        
        # Process scraped deadlines
        created_count = 0
        updated_count = 0
        errors = []
        
        for scraped_deadline in scraped_deadlines:
            try:
                # Check if deadline already exists
                existing_deadline = db.query(Deadline).filter(
                    and_(
                        Deadline.user_id == user.id,
                        Deadline.portal_id == portal.id,
                        Deadline.portal_task_id == scraped_deadline.id
                    )
                ).first()
                
                if existing_deadline:
                    # Update existing deadline
                    existing_deadline.title = scraped_deadline.title
                    existing_deadline.description = scraped_deadline.description
                    existing_deadline.due_date = scraped_deadline.due_date
                    existing_deadline.priority = scraped_deadline.priority
                    existing_deadline.portal_url = scraped_deadline.url
                    existing_deadline.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                    logger.debug(f"Updated deadline: {scraped_deadline.title}")
                    
                else:
                    # Create new deadline
                    new_deadline = Deadline(
                        user_id=user.id,
                        portal_id=portal.id,
                        title=scraped_deadline.title,
                        description=scraped_deadline.description,
                        due_date=scraped_deadline.due_date,
                        priority=scraped_deadline.priority,
                        portal_task_id=scraped_deadline.id,
                        portal_url=scraped_deadline.url,
                        status="pending"
                    )
                    db.add(new_deadline)
                    created_count += 1
                    logger.debug(f"Created deadline: {scraped_deadline.title}")
                
            except Exception as e:
                logger.error(f"Failed to process deadline {scraped_deadline.title}: {e}")
                errors.append(f"Failed to process {scraped_deadline.title}: {str(e)}")
        
        # Update portal last sync
        portal.last_sync = datetime.utcnow()
        db.commit()
        
        result = {
            "success": True,
            "portal_id": portal_id,
            "created": created_count,
            "updated": updated_count,
            "total_scraped": len(scraped_deadlines),
            "errors": errors
        }
        
        logger.info(f"Scraping completed for portal {portal_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error scraping portal {portal_id}: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.scraping_tasks.scrape_user_portals')
def scrape_user_portals(self, user_id: int):
    """
    Scrape all portals for a specific user.
    
    Args:
        user_id: ID of the user whose portals to scrape
        
    Returns:
        Dict with aggregated scraping results
    """
    db = get_db_session()
    try:
        # Get user's portals
        portals = db.query(Portal).filter(
            and_(Portal.user_id == user_id, Portal.is_active == True)
        ).all()
        
        if not portals:
            return {"success": True, "message": f"No active portals found for user {user_id}"}
        
        results = []
        total_created = 0
        total_updated = 0
        total_errors = []
        
        # Scrape each portal
        for portal in portals:
            logger.info(f"Scraping portal {portal.id} for user {user_id}")
            result = scrape_portal.apply(args=[portal.id])
            
            if result.successful():
                portal_result = result.result
                results.append(portal_result)
                
                if portal_result.get("success"):
                    total_created += portal_result.get("created", 0)
                    total_updated += portal_result.get("updated", 0)
                    total_errors.extend(portal_result.get("errors", []))
                else:
                    total_errors.append(f"Portal {portal.id}: {portal_result.get('error', 'Unknown error')}")
            else:
                logger.error(f"Task failed for portal {portal.id}: {result.traceback}")
                total_errors.append(f"Portal {portal.id}: Task execution failed")
        
        return {
            "success": True,
            "user_id": user_id,
            "portals_scraped": len(portals),
            "total_created": total_created,
            "total_updated": total_updated,
            "total_errors": len(total_errors),
            "errors": total_errors,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error scraping portals for user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.scraping_tasks.scrape_all_portals')
def scrape_all_portals(self):
    """
    Scrape all active portals in the system.
    
    Returns:
        Dict with system-wide scraping results
    """
    db = get_db_session()
    try:
        # Get all active portals
        portals = db.query(Portal).filter(Portal.is_active == True).all()
        
        if not portals:
            return {"success": True, "message": "No active portals found"}
        
        logger.info(f"Starting system-wide scraping for {len(portals)} portals")
        
        results = []
        total_created = 0
        total_updated = 0
        total_errors = []
        
        # Group portals by user for better organization
        user_portals = {}
        for portal in portals:
            if portal.user_id not in user_portals:
                user_portals[portal.user_id] = []
            user_portals[portal.user_id].append(portal)
        
        # Scrape each user's portals
        for user_id, user_portal_list in user_portals.items():
            logger.info(f"Scraping {len(user_portal_list)} portals for user {user_id}")
            
            for portal in user_portal_list:
                result = scrape_portal.apply(args=[portal.id])
                
                if result.successful():
                    portal_result = result.result
                    results.append(portal_result)
                    
                    if portal_result.get("success"):
                        total_created += portal_result.get("created", 0)
                        total_updated += portal_result.get("updated", 0)
                        total_errors.extend(portal_result.get("errors", []))
                    else:
                        total_errors.append(f"Portal {portal.id}: {portal_result.get('error', 'Unknown error')}")
                else:
                    logger.error(f"Task failed for portal {portal.id}: {result.traceback}")
                    total_errors.append(f"Portal {portal.id}: Task execution failed")
        
        result = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "portals_scraped": len(portals),
            "users_affected": len(user_portals),
            "total_created": total_created,
            "total_updated": total_updated,
            "total_errors": len(total_errors),
            "errors": total_errors[:10],  # Limit errors to prevent huge responses
            "summary": f"Scraped {len(portals)} portals, created {total_created} deadlines, updated {total_updated} deadlines"
        }
        
        logger.info(f"System-wide scraping completed: {result['summary']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in system-wide scraping: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.scraping_tasks.sync_portal_deadlines')
def sync_portal_deadlines(self, portal_id: int, force_update: bool = False):
    """
    Sync deadlines for a portal, with option to force update all deadlines.
    
    Args:
        portal_id: ID of the portal to sync
        force_update: If True, update all deadlines regardless of modification time
        
    Returns:
        Dict with sync results
    """
    db = get_db_session()
    try:
        portal = db.query(Portal).filter(Portal.id == portal_id).first()
        if not portal:
            return {"success": False, "error": "Portal not found"}
        
        # Check if portal was recently synced (unless forced)
        if not force_update and portal.last_sync:
            time_since_sync = datetime.utcnow() - portal.last_sync
            if time_since_sync < timedelta(minutes=10):  # Don't sync more than once every 10 minutes
                return {
                    "success": True,
                    "message": f"Portal {portal_id} was recently synced, skipping",
                    "last_sync": portal.last_sync.isoformat()
                }
        
        # Perform the scraping
        result = scrape_portal.apply(args=[portal_id])
        
        if result.successful():
            return result.result
        else:
            logger.error(f"Sync failed for portal {portal_id}: {result.traceback}")
            return {"success": False, "error": "Task execution failed"}
        
    except Exception as e:
        logger.error(f"Error syncing portal {portal_id}: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.scraping_tasks.cleanup_orphaned_deadlines')
def cleanup_orphaned_deadlines(self):
    """
    Clean up deadlines that no longer exist in their source portals.
    
    Returns:
        Dict with cleanup results
    """
    db = get_db_session()
    try:
        # Find deadlines older than 24 hours that haven't been updated
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        old_deadlines = db.query(Deadline).filter(
            and_(
                Deadline.portal_id.isnot(None),  # Only portal-sourced deadlines
                Deadline.updated_at < cutoff_time,
                Deadline.status != "completed"
            )
        ).all()
        
        if not old_deadlines:
            return {"success": True, "message": "No orphaned deadlines found"}
        
        # For each deadline, check if it still exists in the portal
        removed_count = 0
        checked_count = 0
        
        for deadline in old_deadlines:
            try:
                # This is a simplified check - in a real implementation,
                # you might want to re-scrape the specific item
                checked_count += 1
                
                # Mark as potentially orphaned if not updated in 7 days
                if deadline.updated_at < (datetime.utcnow() - timedelta(days=7)):
                    # Add a tag or status to indicate it might be orphaned
                    deadline.description = (deadline.description or "") + "\n[WARNING: May be orphaned - not found in recent sync]"
                    deadline.updated_at = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Error checking deadline {deadline.id}: {e}")
        
        db.commit()
        
        return {
            "success": True,
            "checked": checked_count,
            "marked_orphaned": removed_count,
            "message": f"Checked {checked_count} old deadlines, marked {removed_count} as potentially orphaned"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning orphaned deadlines: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()