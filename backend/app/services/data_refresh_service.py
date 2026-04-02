"""
Data Refresh Service
Handles automatic Ingestion-agent refresh and optional Google Sheets cache refresh.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from .google_sheets_data_service import get_service as get_gs_service
from .cache_service import get_cache
from .ingestion_bridge import run_ingestion_once, get_loader_processor

loader, processor = get_loader_processor()

logger = logging.getLogger(__name__)


class DataRefreshService:
    """Service to refresh ingestion data and cache data sources."""

    @staticmethod
    def refresh_ingestion_data() -> Dict[str, Any]:
        """Run one Ingestion-agent pipeline cycle."""
        result = {
            'timestamp': datetime.now().isoformat(),
            'successful': [],
            'failed': [],
            'errors': {}
        }

        try:
            success = run_ingestion_once()
            if success:
                result['successful'].append('ingestion_pipeline')
                logger.info("Ingestion pipeline refresh completed successfully")
            else:
                result['failed'].append('ingestion_pipeline')
                result['errors']['ingestion_pipeline'] = 'Pipeline reported failures'
                logger.warning("Ingestion pipeline refresh completed with failures")
        except Exception as exc:
            result['failed'].append('ingestion_pipeline')
            result['errors']['ingestion_pipeline'] = str(exc)
            logger.exception("Failed to run ingestion pipeline refresh")

        return result
    
    @staticmethod
    def refresh_all_data() -> Dict[str, Any]:
        """
        Refresh ingestion source data and then refresh Google Sheets cache.
        Ingestion-agent remains the primary source of truth.
        
        Returns:
            Dictionary with refresh status and any errors
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'successful': [],
            'failed': [],
            'errors': {}
        }

        ingestion_result = DataRefreshService.refresh_ingestion_data()
        results['successful'].extend(ingestion_result['successful'])
        results['failed'].extend(ingestion_result['failed'])
        results['errors'].update(ingestion_result['errors'])
        
        try:
            # Get services
            gs_service = get_gs_service()
            cache = get_cache()
            
            # Check if Google Sheets service is authenticated
            if not gs_service.is_authenticated():
                logger.warning("Google Sheets service not authenticated")
                results['errors']['auth'] = gs_service.get_last_error()
                
                # Try to use cached data as fallback
                logger.info("Attempting to use cached data as fallback")
                for key in ['unified_solar', 'last_7_days', 'smb_status']:
                    cached = cache.get(key)
                    if cached:
                        results['successful'].append(f"{key} (from cache)")
                
                return results
            
            # Refresh unified solar data
            try:
                logger.info("Refreshing unified solar data...")
                unified_df = gs_service.get_unified_solar_data()
                if unified_df is not None and not unified_df.empty:
                    cache.set('unified_solar', unified_df, ttl_seconds=600)
                    results['successful'].append('unified_solar')
                    logger.info(f"Refreshed unified solar data ({len(unified_df)} rows)")
                else:
                    results['failed'].append('unified_solar')
                    results['errors']['unified_solar'] = 'No data returned'
            except Exception as e:
                logger.error(f"Failed to refresh unified solar data: {e}")
                results['failed'].append('unified_solar')
                results['errors']['unified_solar'] = str(e)
            
            # Refresh 7-day data
            try:
                logger.info("Refreshing 7-day data...")
                days_7_df = gs_service.get_last_7_days_data()
                if days_7_df is not None and not days_7_df.empty:
                    cache.set('last_7_days', days_7_df, ttl_seconds=600)
                    results['successful'].append('last_7_days')
                    logger.info(f"Refreshed 7-day data ({len(days_7_df)} rows)")
                else:
                    results['failed'].append('last_7_days')
                    results['errors']['last_7_days'] = 'No data returned'
            except Exception as e:
                logger.error(f"Failed to refresh 7-day data: {e}")
                results['failed'].append('last_7_days')
                results['errors']['last_7_days'] = str(e)
            
            # Refresh SMB status data
            try:
                logger.info("Refreshing SMB status data...")
                smb_df = gs_service.get_smb_status_data()
                if smb_df is not None and not smb_df.empty:
                    cache.set('smb_status', smb_df, ttl_seconds=600)
                    results['successful'].append('smb_status')
                    logger.info(f"Refreshed SMB status data ({len(smb_df)} rows)")
                else:
                    results['failed'].append('smb_status')
                    results['errors']['smb_status'] = 'No data returned'
            except Exception as e:
                logger.error(f"Failed to refresh SMB status data: {e}")
                results['failed'].append('smb_status')
                results['errors']['smb_status'] = str(e)
            
            # Log refresh completion
            total = len(results['successful']) + len(results['failed'])
            logger.info(f"Data refresh complete: {len(results['successful'])}/{total} sources updated")
            
        except Exception as e:
            logger.error(f"Unexpected error in data refresh: {e}")
            results['errors']['general'] = str(e)
        
        return results
    
    @staticmethod
    def get_unified_data_with_fallback(
        config: Dict[str, Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get unified data from cache or fallback to loader
        
        Args:
            config: Configuration dictionary
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with data, date_range, and total_records
        """
        cache = get_cache()
        
        try:
            # Try to get from cache
            cached_data = cache.get('unified_solar', for_frontend=True)
            
            if cached_data:
                if isinstance(cached_data, list):
                    df = pd.DataFrame(cached_data)
                    logger.info(f"Using cached unified solar data ({len(df)} rows)")
                else:
                    df = cached_data
            else:
                # Fallback to loader
                logger.info("Cache miss for unified data, falling back to loader")
                grid_df = loader.load_grid_data(config)
                solar_df = loader.load_solar_data(config)
                diesel_df = loader.load_diesel_data(config)
                df = processor.build_unified_dataframe(grid_df, solar_df, diesel_df)
            
            # Filter by date if provided
            if start_date or end_date:
                df['Date'] = pd.to_datetime(df['Date'])
                if start_date:
                    df = df[df['Date'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['Date'] <= pd.to_datetime(end_date)]
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # Get date range
            all_dates = pd.to_datetime(df['Date'])
            date_range = {
                "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
                "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
            }
            
            # Drop unnecessary columns
            df = df.drop(
                columns=["Irradiance (W/m²)", "DG Runtime (hrs)", "Source"],
                errors="ignore",
            )
            
            data = df.to_dict('records')
            
            return {
                "data": data,
                "date_range": date_range,
                "total_records": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error getting unified data: {e}")
            return {
                "data": [],
                "date_range": {"min_date": None, "max_date": None},
                "total_records": 0,
                "error": str(e)
            }
    
    @staticmethod
    def get_solar_data_with_fallback(
        config: Dict[str, Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get solar data from cache or fallback"""
        cache = get_cache()
        
        try:
            # Try cache first
            cached_data = cache.get('last_7_days', for_frontend=True)
            
            if cached_data:
                if isinstance(cached_data, list):
                    df = pd.DataFrame(cached_data)
                    logger.info(f"Using cached solar data ({len(df)} rows)")
                else:
                    df = cached_data
            else:
                # Fallback to loader
                logger.info("Cache miss for solar data, falling back to loader")
                df = loader.load_solar_data(config)
            
            # Filter by date if provided
            if start_date or end_date:
                df['Date'] = pd.to_datetime(df['Date'])
                if start_date:
                    df = df[df['Date'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['Date'] <= pd.to_datetime(end_date)]
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # Get date range
            all_dates = pd.to_datetime(df['Date'])
            date_range = {
                "min_date": all_dates.min().strftime('%Y-%m-%d') if len(all_dates) > 0 else None,
                "max_date": all_dates.max().strftime('%Y-%m-%d') if len(all_dates) > 0 else None
            }
            
            data = df.to_dict('records')
            
            return {
                "data": data,
                "date_range": date_range,
                "total_records": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error getting solar data: {e}")
            return {
                "data": [],
                "date_range": {"min_date": None, "max_date": None},
                "total_records": 0,
                "error": str(e)
            }

