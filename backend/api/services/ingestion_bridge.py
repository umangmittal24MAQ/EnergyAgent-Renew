"""
Bridge helpers for loading and running the Ingestion-agent modules.

The source folder name contains a hyphen (Ingestion-agent), so regular
package imports are not reliable. This module loads the scripts directly
from file paths and exposes stable accessors for API services.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

INGESTION_AGENT_DIR = Path(__file__).parent.parent.parent / "energy-dashboard" / "Ingestion-agent"

_MODULE_CACHE: Dict[str, ModuleType] = {}


def _load_module(module_name: str, file_name: str) -> ModuleType:
    """Load a Python module from the Ingestion-agent directory."""
    if module_name in _MODULE_CACHE:
        return _MODULE_CACHE[module_name]

    file_path = INGESTION_AGENT_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"Ingestion-agent module file not found: {file_path}")

    # Ensure local imports like `import scrape` resolve from Ingestion-agent.
    ingestion_path = str(INGESTION_AGENT_DIR)
    if ingestion_path not in sys.path:
        sys.path.insert(0, ingestion_path)

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec for {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE_CACHE[module_name] = module
    return module


def get_loader_processor() -> Tuple[ModuleType, ModuleType]:
    """Return loaded loader and processor modules from Ingestion-agent."""
    loader = _load_module("ingestion_agent_loader", "loader.py")
    processor = _load_module("ingestion_agent_processor", "processor.py")
    return loader, processor


def run_ingestion_once() -> bool:
    """Execute one ingestion run via ingestion_orchestrator.run_once()."""
    orchestrator = _load_module("ingestion_agent_orchestrator", "ingestion_orchestrator.py")

    if not hasattr(orchestrator, "run_once"):
        raise AttributeError("ingestion_orchestrator.py does not define run_once()")

    logger.info("Triggering one-time ingestion pipeline run")
    return bool(orchestrator.run_once())


def run_inverter_backfill_once() -> bool:
    """Execute one-time INV_1..INV_5 backfill on existing master-grid rows."""
    writer_module = _load_module("ingestion_agent_google_sheets_writer", "google_sheets_writer.py")

    if not hasattr(writer_module, "backfill_inverter_columns"):
        raise AttributeError("google_sheets_writer.py does not define backfill_inverter_columns()")

    logger.info("Triggering one-time inverter column backfill")
    return bool(writer_module.backfill_inverter_columns())


def get_ingestion_agent_dir() -> Path:
    """Expose the configured Ingestion-agent directory."""
    return INGESTION_AGENT_DIR
