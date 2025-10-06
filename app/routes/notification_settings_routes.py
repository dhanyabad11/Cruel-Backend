from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_supabase_client
from app.auth_deps import get_current_user
from app.schemas.notification_settings import (
    NotificationSettingsCreate,
    NotificationSettingsUpdate, 
    NotificationSettingsResponse,
    NotificationReminderCreate,
    NotificationReminderUpdate,
    NotificationReminderResponse,
    NotificationSettingsWithReminders,
    BulkReminderUpdate
)
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/settings", tags=["notification-settings"])

@router.get("/notifications")
async def get_notification_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get user's notification settings with all reminder configurations"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    # Get existing settings
    settings_result = supabase.table("notification_settings").select("*").eq("user_id", user_id).execute()
    
    if not settings_result.data:
        # Create default settings if they don't exist
        default_settings = {
            "user_id": user_id,
            "email": current_user.get("email"),
            "phone_number": None,
            "whatsapp_number": None,
            "email_enabled": True,
            "sms_enabled": False,
            "whatsapp_enabled": False,
            "push_enabled": True
        }
        
        insert_result = supabase.table("notification_settings").insert(default_settings).execute()
        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to create notification settings")
        settings = insert_result.data[0]
    else:
        settings = settings_result.data[0]
    
    # Get all reminder configurations
    reminders_result = supabase.table("notification_reminders").select("*").eq("user_id", user_id).execute()
    reminders = reminders_result.data or []
    
    # If no reminders exist, create default one
    if not reminders:
        default_reminder = {
            "user_id": user_id,
            "reminder_time": "1_day",
            "email_enabled": True,
            "sms_enabled": False,
            "whatsapp_enabled": False,
            "push_enabled": True
        }
        reminder_insert = supabase.table("notification_reminders").insert(default_reminder).execute()
        if reminder_insert.data:
            reminders = reminder_insert.data
    
    return {
        "settings": settings,
        "reminders": reminders
    }

@router.put("/notifications")
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update notification settings"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    # Update only provided fields
    settings_dict = settings_data.dict(exclude_unset=True)
    settings_dict["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.table("notification_settings").upsert(
        {**settings_dict, "user_id": user_id},
        on_conflict="user_id"
    ).execute()
    
    if result.data:
        return result.data[0]
    else:
        raise HTTPException(status_code=500, detail="Failed to update notification settings")

@router.get("/reminders")
async def get_notification_reminders(
    current_user: dict = Depends(get_current_user)
):
    """Get all notification reminder configurations"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    result = supabase.table("notification_reminders").select("*").eq("user_id", user_id).order("reminder_time").execute()
    return result.data or []

@router.post("/reminders")
async def create_notification_reminder(
    reminder_data: NotificationReminderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create or update a notification reminder configuration"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    reminder_dict = reminder_data.dict()
    reminder_dict["user_id"] = user_id
    
    # Use upsert to create or update
    result = supabase.table("notification_reminders").upsert(
        reminder_dict,
        on_conflict="user_id,reminder_time"
    ).execute()
    
    if result.data:
        return result.data[0]
    else:
        raise HTTPException(status_code=500, detail="Failed to create reminder")

@router.put("/reminders/bulk")
async def update_bulk_reminders(
    bulk_update: BulkReminderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update multiple reminder configurations at once"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    # First, delete all existing reminders for the user
    supabase.table("notification_reminders").delete().eq("user_id", user_id).execute()
    
    # Then insert all new reminders
    reminders_to_insert = []
    for reminder in bulk_update.reminders:
        reminder_dict = reminder.dict()
        reminder_dict["user_id"] = user_id
        reminders_to_insert.append(reminder_dict)
    
    if reminders_to_insert:
        result = supabase.table("notification_reminders").insert(reminders_to_insert).execute()
        return result.data
    else:
        return []

@router.delete("/reminders/{reminder_time}")
async def delete_notification_reminder(
    reminder_time: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific reminder configuration"""
    user_id = current_user.get("id") or current_user.get("sub")
    supabase = get_supabase_client()
    
    result = supabase.table("notification_reminders").delete().eq("user_id", user_id).eq("reminder_time", reminder_time).execute()
    
    if result.data:
        return {"message": f"Reminder for {reminder_time} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Reminder not found")