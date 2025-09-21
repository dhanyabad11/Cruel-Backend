"""
Maintenance Tasks

Background tasks for system maintenance and cleanup operations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text, or_

from app.database import SessionLocal
from app.models import User, Deadline, Notification, Portal

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for tasks"""
    return SessionLocal()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.cleanup_old_notifications')
def cleanup_old_notifications(self, days_to_keep: int = 30):
    """
    Clean up old notification records.
    
    Args:
        days_to_keep: Number of days of notifications to keep
        
    Returns:
        Dict with cleanup results
    """
    db = get_db_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count notifications to be deleted
        old_notifications = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        )
        
        count_to_delete = old_notifications.count()
        
        if count_to_delete == 0:
            return {
                "success": True,
                "message": f"No notifications older than {days_to_keep} days found"
            }
        
        # Delete old notifications
        deleted_count = old_notifications.delete()
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Deleted {deleted_count} notifications older than {days_to_keep} days"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.cleanup_completed_deadlines')
def cleanup_completed_deadlines(self, days_to_keep: int = 90):
    """
    Clean up old completed deadlines.
    
    Args:
        days_to_keep: Number of days of completed deadlines to keep
        
    Returns:
        Dict with cleanup results
    """
    db = get_db_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count completed deadlines to be deleted
        old_completed = db.query(Deadline).filter(
            and_(
                Deadline.status == "completed",
                Deadline.updated_at < cutoff_date
            )
        )
        
        count_to_delete = old_completed.count()
        
        if count_to_delete == 0:
            return {
                "success": True,
                "message": f"No completed deadlines older than {days_to_keep} days found"
            }
        
        # Delete old completed deadlines
        deleted_count = old_completed.delete()
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old completed deadlines")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Deleted {deleted_count} completed deadlines older than {days_to_keep} days"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up completed deadlines: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.update_portal_sync_status')
def update_portal_sync_status(self):
    """
    Update portal sync status and identify stale portals.
    
    Returns:
        Dict with sync status update results
    """
    db = get_db_session()
    try:
        # Find portals that haven't been synced recently
        stale_threshold = datetime.utcnow() - timedelta(hours=2)
        
        stale_portals = db.query(Portal).filter(
            and_(
                Portal.is_active == True,
                or_(
                    Portal.last_sync < stale_threshold,
                    Portal.last_sync.is_(None)
                )
            )
        ).all()
        
        # Update portal status
        updated_count = 0
        for portal in stale_portals:
            # Check if portal is having sync issues
            if portal.last_sync and (datetime.utcnow() - portal.last_sync) > timedelta(days=1):
                # Mark as potentially problematic
                portal.sync_status = "stale"
                updated_count += 1
            elif not portal.last_sync:
                portal.sync_status = "never_synced"
                updated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "stale_portals_found": len(stale_portals),
            "portals_updated": updated_count,
            "message": f"Updated status for {updated_count} stale portals"
        }
        
    except Exception as e:
        logger.error(f"Error updating portal sync status: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.generate_system_stats')
def generate_system_stats(self):
    """
    Generate system usage statistics.
    
    Returns:
        Dict with system statistics
    """
    db = get_db_session()
    try:
        # User statistics
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        
        # Deadline statistics
        total_deadlines = db.query(func.count(Deadline.id)).scalar()
        pending_deadlines = db.query(func.count(Deadline.id)).filter(Deadline.status == "pending").scalar()
        completed_deadlines = db.query(func.count(Deadline.id)).filter(Deadline.status == "completed").scalar()
        overdue_deadlines = db.query(func.count(Deadline.id)).filter(Deadline.status == "overdue").scalar()
        
        # Portal statistics
        total_portals = db.query(func.count(Portal.id)).scalar()
        active_portals = db.query(func.count(Portal.id)).filter(Portal.is_active == True).scalar()
        
        # Portal type breakdown
        portal_types = db.query(
            Portal.portal_type,
            func.count(Portal.id)
        ).filter(Portal.is_active == True).group_by(Portal.portal_type).all()
        
        # Notification statistics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_notifications = db.query(func.count(Notification.id)).filter(
            Notification.created_at >= thirty_days_ago
        ).scalar()
        
        successful_notifications = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.created_at >= thirty_days_ago,
                Notification.status.in_(["sent", "delivered"])
            )
        ).scalar()
        
        failed_notifications = db.query(func.count(Notification.id)).filter(
            and_(
                Notification.created_at >= thirty_days_ago,
                Notification.status == "failed"
            )
        ).scalar()
        
        # Calculate success rate
        success_rate = (successful_notifications / recent_notifications * 100) if recent_notifications > 0 else 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_deadlines = db.query(func.count(Deadline.id)).filter(
            Deadline.created_at >= seven_days_ago
        ).scalar()
        
        recent_sync_activity = db.query(func.count(Portal.id)).filter(
            Portal.last_sync >= seven_days_ago
        ).scalar()
        
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "deadlines": {
                "total": total_deadlines,
                "pending": pending_deadlines,
                "completed": completed_deadlines,
                "overdue": overdue_deadlines
            },
            "portals": {
                "total": total_portals,
                "active": active_portals,
                "inactive": total_portals - active_portals,
                "by_type": {pt.value: count for pt, count in portal_types}
            },
            "notifications_30d": {
                "total": recent_notifications,
                "successful": successful_notifications,
                "failed": failed_notifications,
                "success_rate": round(success_rate, 2)
            },
            "recent_activity_7d": {
                "new_deadlines": recent_deadlines,
                "portals_synced": recent_sync_activity
            }
        }
        
        logger.info(f"Generated system stats: {stats}")
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error generating system stats: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.health_check')
def health_check(self):
    """
    Perform system health check.
    
    Returns:
        Dict with health check results
    """
    db = get_db_session()
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Database connectivity check
        try:
            db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check for recent portal sync activity
        try:
            recent_sync = db.query(Portal).filter(
                Portal.last_sync >= (datetime.utcnow() - timedelta(hours=1))
            ).count()
            
            if recent_sync > 0:
                health_status["checks"]["portal_sync"] = "healthy"
            else:
                health_status["checks"]["portal_sync"] = "warning: no recent sync activity"
        except Exception as e:
            health_status["checks"]["portal_sync"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check for recent notification activity
        try:
            recent_notifications = db.query(Notification).filter(
                Notification.created_at >= (datetime.utcnow() - timedelta(hours=1))
            ).count()
            
            health_status["checks"]["notifications"] = f"processed {recent_notifications} in last hour"
        except Exception as e:
            health_status["checks"]["notifications"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check notification service
        try:
            from app.services.notification_service import get_notification_service
            notification_service = get_notification_service()
            
            if notification_service and notification_service.validate_config():
                health_status["checks"]["notification_service"] = "healthy"
            else:
                health_status["checks"]["notification_service"] = "warning: not configured or invalid"
        except Exception as e:
            health_status["checks"]["notification_service"] = f"unhealthy: {str(e)}"
        
        return {
            "success": True,
            "health": health_status
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "success": False,
            "error": str(e),
            "health": {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "unhealthy",
                "checks": {"general": f"health check failed: {str(e)}"}
            }
        }
    
    finally:
        db.close()


@shared_task(bind=True, name='app.tasks.maintenance_tasks.optimize_database')
def optimize_database(self):
    """
    Perform database optimization operations.
    
    Returns:
        Dict with optimization results
    """
    db = get_db_session()
    try:
        optimization_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": []
        }
        
        # SQLite-specific optimizations
        try:
            # Analyze tables for query optimization
            db.execute(text("ANALYZE"))
            optimization_results["operations"].append("ANALYZE completed")
            
            # Vacuum to reclaim space
            db.execute(text("VACUUM"))
            optimization_results["operations"].append("VACUUM completed")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
            optimization_results["operations"].append(f"Error: {str(e)}")
        
        return {
            "success": True,
            "optimization": optimization_results
        }
        
    except Exception as e:
        logger.error(f"Error in database optimization: {e}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()