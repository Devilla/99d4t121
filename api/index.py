"""Vercel Python Function entrypoint.

Vercel's Python runtime looks for a top-level `app` (ASGI) or `handler`
object in this file. We just re-export the real FastAPI app that lives in
backend/app/main.py, so there is exactly one copy of the application code.
"""
import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from app.main import app  # noqa: E402  (import after sys.path setup, by design)

__all__ = ["app"]
