"""
DAO GolemDB Interface Backend

This backend integrates the original uploader.py and receiver.py logic
into a modern, modular architecture with FastAPI REST API.

Key components:
- services/: Business logic (upload, download, search)
- api/: REST API endpoints
- core/: Interfaces, configuration, exceptions
"""

__version__ = "0.1.0"
__author__ = "DAO GolemDB Team"
__description__ = "Backend for DAO GolemDB Interface"