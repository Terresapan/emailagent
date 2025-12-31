"""Database connection and session management.

This module re-exports from the shared db package for backward compatibility.
"""
from db import (
    DATABASE_URL,
    engine,
    SessionLocal,
    Base,
    get_db,
    init_db,
)

__all__ = [
    "DATABASE_URL",
    "engine", 
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
]
