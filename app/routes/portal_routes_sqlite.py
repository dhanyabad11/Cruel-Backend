from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import sqlite3

router = APIRouter()

@router.get("/")
async def get_portals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    portal_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all portals"""
    conn = sqlite3.connect('ai_cruel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM portals"
    params = []
    
    where_clauses = []
    if portal_type:
        where_clauses.append("portal_type = ?")
        params.append(portal_type)
    if is_active is not None:
        where_clauses.append("is_active = ?")
        params.append(is_active)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += f" LIMIT {limit} OFFSET {skip}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    portals = []
    for row in rows:
        portals.append({
            "id": row["id"],
            "name": row["name"],
            "portal_type": row["portal_type"],
            "url": row["url"],
            "username": row["username"],
            "password": row["password"],
            "api_key": row["api_key"],
            "config": row["config"],
            "is_active": bool(row["is_active"]),
            "last_sync": row["last_sync"],
            "user_id": row["user_id"],
            "created_at": row["created_at"]
        })
    
    return portals

@router.post("/")
async def create_portal(portal_data: dict):
    """Create a new portal"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO portals (name, portal_type, url, username, password, api_key, config, is_active, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        portal_data.get("name"),
        portal_data.get("portal_type"),
        portal_data.get("url"),
        portal_data.get("username", ""),
        portal_data.get("password", ""),
        portal_data.get("api_key", ""),
        portal_data.get("config", "{}"),
        portal_data.get("is_active", True),
        1  # Default user
    ))
    
    portal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": portal_id, **portal_data}

@router.get("/{portal_id}")
async def get_portal(portal_id: int):
    """Get a specific portal by ID"""
    conn = sqlite3.connect('ai_cruel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM portals WHERE id = ?", (portal_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Portal not found")
    
    return {
        "id": row["id"],
        "name": row["name"],
        "portal_type": row["portal_type"],
        "url": row["url"],
        "username": row["username"],
        "password": row["password"],
        "api_key": row["api_key"],
        "config": row["config"],
        "is_active": bool(row["is_active"]),
        "last_sync": row["last_sync"],
        "user_id": row["user_id"],
        "created_at": row["created_at"]
    }

@router.put("/{portal_id}")
async def update_portal(portal_id: int, portal_data: dict):
    """Update a specific portal"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    # Check if portal exists
    cursor.execute("SELECT id FROM portals WHERE id = ?", (portal_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Portal not found")
    
    # Update fields
    update_fields = []
    params = []
    
    for field in ["name", "portal_type", "url", "username", "password", "api_key", "config", "is_active"]:
        if field in portal_data:
            update_fields.append(f"{field} = ?")
            params.append(portal_data[field])
    
    if update_fields:
        params.append(portal_id)
        query = f"UPDATE portals SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
    
    conn.commit()
    conn.close()
    
    return {"id": portal_id, **portal_data}

@router.delete("/{portal_id}")
async def delete_portal(portal_id: int):
    """Delete a specific portal"""
    conn = sqlite3.connect('ai_cruel.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM portals WHERE id = ?", (portal_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Portal not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Portal deleted successfully"}