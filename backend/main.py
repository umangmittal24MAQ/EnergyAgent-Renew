"""
Entry point for the Energy Dashboard backend application
"""
import uvicorn
from app.api.main import create_app
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.api.main:create_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        env_file=".env",
    )
