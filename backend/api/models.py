"""SQLAlchemy models for email and digest storage.

This module re-exports from the shared db package for backward compatibility.
"""
from db import Digest, Email

__all__ = ["Digest", "Email"]
