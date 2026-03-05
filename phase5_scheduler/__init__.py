"""
Phase 5: Autonomous Scheduler Module

This module handles automated data synchronization for the RAG Mutual Fund FAQ Chatbot.
It orchestrates Phase 1 (Data Acquisition) and Phase 2 (Knowledge Base Indexing)
to ensure data freshness.

Usage:
    - Run manually: python -m phase5_scheduler.scheduler
    - Use APScheduler for automated runs
    - Import MFDataScheduler for custom scheduling
"""

from .scheduler import MFDataScheduler, trigger_full_update

__all__ = ['MFDataScheduler', 'trigger_full_update']
