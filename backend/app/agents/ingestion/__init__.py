"""
Data Ingestion Agent Module
Consolidates all data ingestion, processing, and export functionality
for the Energy Dashboard Backend API
"""

from . import loader
from . import processor
from . import exporter

__all__ = ['loader', 'processor', 'exporter']
__version__ = '1.0.0'
