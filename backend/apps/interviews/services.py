"""Backward-compatible imports for interview service helpers."""

from .calendar_service import build_local_calendar_link as build_calendar_link

__all__ = ['build_calendar_link']
