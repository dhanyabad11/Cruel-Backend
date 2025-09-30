"""
WhatsApp integration routes for AI Cruel
Handles WhatsApp chat uploads and deadline extraction
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import tempfile
import os
from datetime import datetime
from supabase import Client

from ..services.whatsapp_parser import WhatsAppChatParser
from ..auth_deps import get_current_user
from ..models.user import User
from ..database import get_supabase_client

router = APIRouter(tags=["whatsapp"])

@router.post("/upload-chat")
async def upload_whatsapp_chat(
    file: UploadFile = File(...),
    auto_create: bool = Form(default=True),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Upload WhatsApp chat export file and extract deadlines

    Args:
        file: WhatsApp chat export (.txt file)
        auto_create: Whether to automatically create deadlines in database
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        List of extracted deadlines with preview
    """
    # Validate file type
    if not file.filename.endswith(('.txt', '.TXT')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported for WhatsApp chat exports"
        )

    # Check file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum 10MB allowed."
        )

    try:
        # Read file content
        content = await file.read()
        chat_text = content.decode('utf-8', errors='ignore')

        # Parse chat for deadlines
        parser = WhatsAppChatParser()
        extracted_deadlines = parser.parse_whatsapp_export(chat_text)

        created_deadlines = []

        if auto_create and extracted_deadlines:
            # Create deadlines in Supabase
            for deadline_data in extracted_deadlines:
                # Only create if confidence is above threshold
                if deadline_data['confidence'] >= 0.6:
                    deadline_insert = {
                        'title': deadline_data['title'][:255],  # Limit title length
                        'description': deadline_data['description'][:1000],  # Limit description
                        'due_date': deadline_data['due_date'].isoformat(),
                        'priority': deadline_data['priority'],
                        'user_id': current_user['id'],
                        'status': 'pending',
                        'source': 'whatsapp',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }

                    result = supabase.table('deadlines').insert(deadline_insert).execute()
                    if result.data:
                        created_deadlines.append({
                            **deadline_data,
                            'created_in_db': True
                        })
                    else:
                        created_deadlines.append({
                            **deadline_data,
                            'created_in_db': False,
                            'reason': 'Failed to create in database'
                        })
                else:
                    created_deadlines.append({
                        **deadline_data,
                        'created_in_db': False,
                        'reason': 'Low confidence score'
                    })
        else:
            # Just return preview without creating
            created_deadlines = [{
                **deadline_data,
                'created_in_db': False,
                'reason': 'Preview mode - auto_create disabled'
            } for deadline_data in extracted_deadlines]

        return {
            "success": True,
            "file_name": file.filename,
            "total_extracted": len(extracted_deadlines),
            "auto_created": len([d for d in created_deadlines if d.get('created_in_db')]),
            "deadlines": created_deadlines,
            "processing_info": {
                "parser_version": "1.0",
                "extraction_timestamp": datetime.now().isoformat(),
                "confidence_threshold": 0.6
            }
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode file. Please ensure it's a valid WhatsApp text export."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat file: {str(e)}"
        )

@router.post("/parse-message")
async def parse_single_message(
    message: str = Form(...),
    sender: str = Form(default="User"),
    auto_create: bool = Form(default=False),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Parse a single message for deadlines

    Args:
        message: The message text to parse
        sender: Who sent the message
        auto_create: Whether to create deadline in database
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Extracted deadlines from the message
    """
    if len(message) < 5:
        raise HTTPException(
            status_code=400,
            detail="Message too short to extract meaningful deadlines"
        )

    try:
        parser = WhatsAppChatParser()
        extracted_deadlines = parser.parse_single_message(message, sender)

        created_deadlines = []

        if auto_create and extracted_deadlines:
            for deadline_data in extracted_deadlines:
                if deadline_data['confidence'] >= 0.5:  # Lower threshold for single messages
                    deadline_insert = {
                        'title': deadline_data['title'][:255],
                        'description': deadline_data['description'][:1000],
                        'due_date': deadline_data['due_date'].isoformat(),
                        'priority': deadline_data['priority'],
                        'user_id': current_user['id'],
                        'status': 'pending',
                        'source': 'whatsapp_message',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }

                    result = supabase.table('deadlines').insert(deadline_insert).execute()
                    if result.data:
                        created_deadlines.append({
                            **deadline_data,
                            'created_in_db': True
                        })

        return {
            "success": True,
            "original_message": message,
            "sender": sender,
            "extracted_deadlines": extracted_deadlines,
            "created_count": len(created_deadlines)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing message: {str(e)}"
        )

@router.get("/examples")
async def get_parsing_examples():
    """
    Get examples of messages that can be parsed for deadlines
    """
    examples = [
        {
            "message": "Don't forget math assignment is due tomorrow at 11:59 PM",
            "expected_extraction": {
                "title": "math assignment",
                "due_date": "tomorrow 11:59 PM",
                "priority": "high"
            }
        },
        {
            "message": "Physics lab report deadline is Friday 5 PM",
            "expected_extraction": {
                "title": "Physics lab report",
                "due_date": "Friday 5 PM", 
                "priority": "medium"
            }
        },
        {
            "message": "Urgent: Submit project proposal by Monday morning",
            "expected_extraction": {
                "title": "project proposal",
                "due_date": "Monday morning",
                "priority": "high"
            }
        },
        {
            "message": "Chemistry exam next Tuesday at 2 PM in room 301",
            "expected_extraction": {
                "title": "Chemistry exam",
                "due_date": "next Tuesday 2 PM",
                "priority": "high"
            }
        },
        {
            "message": "History essay due next week, no rush",
            "expected_extraction": {
                "title": "History essay",
                "due_date": "next week",
                "priority": "low"
            }
        }
    ]
    
    return {
        "examples": examples,
        "supported_formats": [
            "Direct deadlines: 'assignment due tomorrow'",
            "Events: 'exam next Friday'", 
            "Submissions: 'submit report by Monday'",
            "Meetings: 'presentation meeting Thursday'",
            "Relative dates: tomorrow, next week, Friday",
            "Priority indicators: urgent, asap, no rush, optional"
        ],
        "tips": [
            "Include specific task names for better extraction",
            "Use clear time expressions (tomorrow, Friday, 5 PM)",
            "Add priority keywords (urgent, optional) when relevant",
            "Longer messages with context work better than short ones"
        ]
    }

@router.post("/bulk-create")
async def bulk_create_deadlines(
    deadlines: List[dict],
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Bulk create deadlines from parsed WhatsApp data

    Args:
        deadlines: List of deadline dictionaries to create
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Summary of created deadlines
    """
    if len(deadlines) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 deadlines can be created at once"
        )

    created_count = 0
    errors = []

    try:
        deadline_inserts = []

        for i, deadline_data in enumerate(deadlines):
            try:
                # Validate required fields
                if not all(k in deadline_data for k in ['title', 'due_date']):
                    errors.append(f"Deadline {i+1}: Missing required fields (title, due_date)")
                    continue

                # Parse due_date if it's a string
                due_date = deadline_data['due_date']
                if isinstance(due_date, str):
                    from dateutil.parser import parse as date_parse
                    due_date = date_parse(due_date)

                deadline_insert = {
                    'title': str(deadline_data['title'])[:255],
                    'description': str(deadline_data.get('description', ''))[:1000],
                    'due_date': due_date.isoformat(),
                    'priority': deadline_data.get('priority', 'medium'),
                    'user_id': current_user['id'],
                    'status': 'pending',
                    'source': deadline_data.get('source', 'whatsapp_bulk'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

                deadline_inserts.append(deadline_insert)
                created_count += 1

            except Exception as e:
                errors.append(f"Deadline {i+1}: {str(e)}")

        if deadline_inserts:
            result = supabase.table('deadlines').insert(deadline_inserts).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create deadlines")

        return {
            "success": True,
            "created_count": created_count,
            "total_submitted": len(deadlines),
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating deadlines: {str(e)}"
        )