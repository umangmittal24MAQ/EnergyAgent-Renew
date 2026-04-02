"""
Bridge helpers for loading and running the Ingestion-agent modules.

The ingestion modules have been restructured as a proper Python package
under app/agents/ingestion/, so this bridge now uses direct imports.
"""
from __future__ import annotations

import logging
from typing import Any, Tuple

logger = logging.getLogger(__name__)


def get_loader_processor() -> Tuple[Any, Any]:
    """Return loaded loader and processor modules from app.agents.ingestion."""
    try:
        from app.agents import ingestion
        return ingestion.loader, ingestion.processor
    except ImportError as e:
        logger.warning(f"Could not import ingestion modules: {e}")
        return None, None





def run_ingestion_once() -> bool:
    """Execute one ingestion run via ingestion_orchestrator.run_once()."""
    try:
        from app.agents.ingestion import ingestion_orchestrator
        if not hasattr(ingestion_orchestrator, "run_once"):
            logger.error("ingestion_orchestrator.py does not define run_once()")
            return False
        logger.info("Triggering one-time ingestion pipeline run")
        return bool(ingestion_orchestrator.run_once())
    except ImportError as e:
        logger.error(f"Failed to import ingestion orchestrator: {e}")
        return False


def run_inverter_backfill_once() -> bool:
    """Execute one-time INV_1..INV_5 backfill on existing master-grid rows."""
    try:
        from app.agents.ingestion import google_sheets_writer
        if not hasattr(google_sheets_writer, "backfill_inverter_columns"):
            logger.error("google_sheets_writer.py does not define backfill_inverter_columns()")
            return False
        logger.info("Triggering one-time inverter column backfill")
        return bool(google_sheets_writer.backfill_inverter_columns())
    except ImportError as e:
        logger.error(f"Failed to import google_sheets_writer: {e}")
        return False


def get_sharepoint_writer():
    """Load and return the SharePoint writer module from ingestion agents."""
    try:
        from app.agents.ingestion import sharepoint_writer
        if not hasattr(sharepoint_writer, "SharePointExcelWriter"):
            logger.error("sharepoint_writer.py does not define SharePointExcelWriter")
            return None
        return sharepoint_writer
    except ImportError:
        logger.warning("SharePoint writer not found. SharePoint functionality disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to load SharePoint writer: {e}")
        return None


def write_to_sharepoint_once(sheet_key: str, data: list) -> bool:
    """
    Write data to SharePoint (single operation)
    
    Args:
        sheet_key: Config key for the sheet (e.g., 'unified_solar')
        data: List of dictionaries to write
        
    Returns:
        True if write successful
    """
    try:
        sharepoint_module = get_sharepoint_writer()
        if not sharepoint_module:
            logger.warning("SharePoint writer not available")
            return False
        
        writer = sharepoint_module.get_sharepoint_writer()
        success = writer.append_data_to_sheet(sheet_key, data)
        
        if success:
            logger.info(f"Successfully wrote {len(data)} rows to SharePoint: {sheet_key}")
        else:
            logger.error(f"Failed to write to SharePoint: {sheet_key}")
        
        return success
    except Exception as e:
        logger.error(f"Exception writing to SharePoint: {e}")
        return False

