#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import asyncio
from pathlib import Path
from loguru import logger

class Launcher:
    def __init__(self):
        self.app_dir = self._get_app_dir()
        self.os_type = platform.system()
        self.is_windows = self.os_type == 'Windows'
        self.is_macos = self.os_type == 'Darwin'
        self.is_linux = self.os_type == 'Linux'
        
        self._setup_logging()
        self._setup_paths()
        
    def _get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent.parent
    
    def _setup_logging(self):
        log_dir = self.app_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'launcher.log'
        logger.add(
            log_file,
            rotation='10 MB',
            retention='7 days',
            level='INFO',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
        )
        logger.info(f"StockMonitor Launcher starting on {self.os_type}")
    
    def _setup_paths(self):
        self.resources_dir = self.app_dir / 'resources'
        self.chrome_extension_dir = self.resources_dir / 'chrome-extension'
        self.csv_data_dir = self.resources_dir / 'csv-data'
        self.configs_dir = self.resources_dir / 'configs'
        self.chromium_dir = self.resources_dir / 'chromium'
        
        self.backend_dir = self.app_dir / 'app'
        
        logger.info(f"App directory: {self.app_dir}")
        logger.info(f"Resources directory: {self.resources_dir}")
    
    def _check_dependencies(self):
        logger.info("Checking dependencies...")
        
        required_dirs = [
            self.resources_dir,
            self.chrome_extension_dir,
            self.csv_data_dir,
            self.configs_dir,
            self.backend_dir,
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.error(f"Required directory not found: {dir_path}")
                return False
        
        logger.info("All required directories found")
        return True
    
    def _setup_environment(self):
        logger.info("Setting up environment variables...")
        
        os.environ['PYTHONPATH'] = str(self.app_dir)
        
        if self.is_windows:
            os.environ['PATH'] = f"{self.app_dir};{os.environ.get('PATH', '')}"
        else:
            os.environ['PATH'] = f"{self.app_dir}:{os.environ.get('PATH', '')}"
        
        os.environ['CSV_DATA_PATH'] = str(self.csv_data_dir)
        os.environ['CHROME_EXTENSION_PATH'] = str(self.chrome_extension_dir)
        os.environ['CONFIG_PATH'] = str(self.configs_dir)
        
        if self.chromium_dir.exists():
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.chromium_dir)
        
        logger.info("Environment variables set successfully")
    
    def _install_playwright_browsers(self):
        logger.info("Checking Playwright browsers...")
        
        if self.chromium_dir.exists() and list(self.chromium_dir.iterdir()):
            logger.info("Chromium already installed")
            return True
        
        logger.info("Installing Playwright browsers...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Playwright browsers installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Playwright browsers: {e}")
            return False
    
    def _load_csv_data(self):
        logger.info("Loading CSV data...")
        
        if not self.csv_data_dir.exists():
            logger.warning("CSV data directory not found, skipping data load")
            return True
        
        csv_files = list(self.csv_data_dir.glob('**/*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files")
        
        return True
    
    def _start_backend_server(self):
        logger.info("Starting backend server...")
        
        try:
            sys.path.insert(0, str(self.app_dir))
            
            from app.main import app
            import uvicorn
            
            host = '0.0.0.0'
            port = 8000
            
            logger.info(f"Starting server on {host}:{port}")
            
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level='info',
                access_log=True
            )
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            raise
    
    async def _initialize_browser_manager(self):
        logger.info("Initializing browser manager...")
        
        try:
            from src.browser_manager import BrowserManager
            
            browser_manager = BrowserManager(
                extension_path=str(self.chrome_extension_dir),
                headless=True
            )
            
            await browser_manager.initialize()
            logger.info("Browser manager initialized successfully")
            
            return browser_manager
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {e}")
            return None
    
    def run(self):
        logger.info("=" * 50)
        logger.info("StockMonitor Launcher")
        logger.info("=" * 50)
        
        if not self._check_dependencies():
            logger.error("Dependency check failed, exiting...")
            sys.exit(1)
        
        self._setup_environment()
        
        if not self._install_playwright_browsers():
            logger.warning("Browser installation failed, continuing anyway...")
        
        if not self._load_csv_data():
            logger.warning("CSV data load failed, continuing anyway...")
        
        try:
            logger.info("Starting application...")
            self._start_backend_server()
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            sys.exit(1)

def main():
    launcher = Launcher()
    launcher.run()

if __name__ == '__main__':
    main()