from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
import sqlite3

router = APIRouter()

@router.get("/")
async def get_deadlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Get all deadlines"""
    conn = sqlite3.connect('ai_cruel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM deadlines"
    params = []
    
    where_clauses = []
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    if priority:
        where_clauses.append("priority = ?")
        params.append(priority)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += f" LIMIT {limit} OFFSET {skip}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    deadlines = []
    for row in rows:
        deadlines.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "due_date": row["due_date"],
            "priority": row["priority"],
            "status": row["status"],
            "portal_id": row["portal_id"],
            "user_id": row["user_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    
    return deadlines

@router.post("/")
async def create_deadline(deadline_data: dict):
    """Create a new deadline"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO deadlines (title, description, due_date, priority, status, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        deadline_data.get("title"),
        deadline_data.get("description"),
        deadline_data.get("due_date"),
        deadline_data.get("priority", "medium"),
        deadline_data.get("status", "pending"),
        1  # Default user
    ))
    
    deadline_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": deadline_id, **deadline_data}

@router.get("/{deadline_id}")
async def get_deadline(deadline_id: int):
    """Get a specific deadline by ID"""
    conn = sqlite3.connect('ai_cruel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM deadlines WHERE id = ?", (deadline_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Deadline not found")
    
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "due_date": row["due_date"],
        "priority": row["priority"],
        "status": row["status"],
        "portal_id": row["portal_id"],
        "user_id": row["user_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

@router.put("/{deadline_id}")
async def update_deadline(deadline_id: int, deadline_data: dict):
    """Update a specific deadline"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    # Check if deadline exists
    cursor.execute("SELECT id FROM deadlines WHERE id = ?", (deadline_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Deadline not found")
    
    # Update fields
    update_fields = []
    params = []
    
    for field in ["title", "description", "due_date", "priority", "status"]:
        if field in deadline_data:
            update_fields.append(f"{field} = ?")
            params.append(deadline_data[field])
    
    if update_fields:
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(deadline_id)
        
        query = f"UPDATE deadlines SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
    
    conn.commit()
    conn.close()
    
    return {"id": deadline_id, **deadline_data}

@router.delete("/{deadline_id}")
async def delete_deadline(deadline_id: int):
    """Delete a specific deadline"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Deadline not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Deadline deleted successfully"}

@router.get("/stats/overview")
async def get_deadline_stats():
    """Get deadline statistics overview"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM deadlines")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as pending FROM deadlines WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as completed FROM deadlines WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as overdue FROM deadlines WHERE status = 'overdue'")
    overdue = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "pending": pending,
        "completed": completed,
        "overdue": overdue,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
    }