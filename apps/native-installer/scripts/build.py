#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from loguru import logger


class BuildManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root.parent / 'stock-monitor-backend'
        self.chrome_extension_dir = self.project_root.parent / 'chrome-extension'
        
        self.build_dir = self.project_root / 'build'
        self.resources_dir = self.project_root / 'resources'
        self.dist_dir = self.project_root / 'dist'
        
        self.os_type = platform.system()
        self.is_windows = self.os_type == 'Windows'
        self.is_macos = self.os_type == 'Darwin'
        self.is_linux = self.os_type == 'Linux'
        
        self._setup_logging()
    
    def _setup_logging(self):
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'build.log'
        logger.add(
            log_file,
            rotation='10 MB',
            retention='7 days',
            level='INFO',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
        )
        logger.info(f"BuildManager initialized on {self.os_type}")
    
    def clean(self):
        logger.info("Cleaning build directories...")
        
        dirs_to_clean = [
            self.build_dir,
            self.dist_dir,
            self.project_root / 'StockMonitor.egg-info',
        ]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Cleaned: {dir_path}")
        
        logger.info("Clean completed")
    
    def prepare_resources(self):
        logger.info("Preparing resources...")
        
        self._prepare_chrome_extension()
        self._prepare_csv_data()
        self._prepare_configs()
        
        logger.info("Resources prepared successfully")
    
    def _prepare_chrome_extension(self):
        logger.info("Preparing Chrome extension...")
        
        target_dir = self.resources_dir / 'chrome-extension'
        
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        if self.chrome_extension_dir.exists():
            shutil.copytree(self.chrome_extension_dir, target_dir)
            logger.info(f"Chrome extension copied to: {target_dir}")
        else:
            logger.warning(f"Chrome extension source not found: {self.chrome_extension_dir}")
    
    def _prepare_csv_data(self):
        logger.info("Preparing CSV data...")
        
        target_dir = self.resources_dir / 'csv-data'
        target_dir.mkdir(parents=True, exist_ok=True)
        
        csv_data_path = os.environ.get('CSV_DATA_PATH_STOCK_DAILY', '/Volumes/MacintoshHD/data/daily')
        
        if Path(csv_data_path).exists():
            csv_files = list(Path(csv_data_path).glob('**/*.csv'))
            logger.info(f"Found {len(csv_files)} CSV files")
            
            for csv_file in csv_files[:10]:
                dest_file = target_dir / csv_file.name
                shutil.copy2(csv_file, dest_file)
                logger.info(f"Copied: {csv_file.name}")
        else:
            logger.warning(f"CSV data path not found: {csv_data_path}")
            logger.info("Creating sample CSV data...")
            
            sample_csv = target_dir / 'sample_stock_data.csv'
            with open(sample_csv, 'w', encoding='utf-8') as f:
                f.write('ts_code,trade_date,open,high,low,close,vol,amount\n')
                f.write('000001.SZ,2024-01-01,10.00,10.50,9.80,10.20,1000000,10200000\n')
            
            logger.info(f"Sample CSV created: {sample_csv}")
    
    def _prepare_configs(self):
        logger.info("Preparing configuration files...")
        
        configs_dir = self.resources_dir / 'configs'
        configs_dir.mkdir(parents=True, exist_ok=True)
        
        env_example = self.backend_dir / '.env.example'
        if env_example.exists():
            shutil.copy2(env_example, configs_dir / '.env.example')
            logger.info("Environment example copied")
        
        crawler_config = self.backend_dir / 'config' / 'crawler_config.yaml'
        if crawler_config.exists():
            shutil.copy2(crawler_config, configs_dir / 'crawler_config.yaml')
            logger.info("Crawler config copied")
    
    def install_dependencies(self):
        logger.info("Installing dependencies...")
        
        requirements_file = self.project_root / 'requirements-installer.txt'
        
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def install_playwright_browsers(self):
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
    
    def build_with_pyinstaller(self):
        logger.info("Building with PyInstaller...")
        
        spec_file = self.project_root / 'pyinstaller.spec'
        
        if not spec_file.exists():
            logger.error(f"PyInstaller spec file not found: {spec_file}")
            return False
        
        try:
            subprocess.run(
                [sys.executable, '-m', 'PyInstaller', str(spec_file), '--clean'],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("PyInstaller build completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"PyInstaller build failed: {e}")
            return False
    
    def build_windows_installer(self):
        logger.info("Building Windows installer...")
        
        if not self.is_windows:
            logger.warning("Not on Windows, skipping Windows installer build")
            return True
        
        dist_dir = self.dist_dir / 'StockMonitor'
        if not dist_dir.exists():
            logger.error(f"Distribution directory not found: {dist_dir}")
            return False
        
        try:
            nsis_script = self._generate_nsis_script()
            nsis_file = self.project_root / 'installer.nsi'
            
            with open(nsis_file, 'w', encoding='utf-8') as f:
                f.write(nsis_script)
            
            logger.info(f"NSIS script generated: {nsis_file}")
            
            subprocess.run(
                ['makensis', str(nsis_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Windows installer built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Windows installer: {e}")
            return False
    
    def _generate_nsis_script(self) -> str:
        return f"""
!define APP_NAME "StockMonitor"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "StockMonitor Team"
!define APP_DIR "$$PROGRAMFILES64\\${{APP_NAME}}"
!define APP_EXECUTABLE "$$APP_DIR\\StockMonitor.exe"

OutFile "dist\\StockMonitor-Setup.exe"
InstallDir ${{APP_DIR}}
RequestExecutionLevel admin
Page directory
Page instfiles

Section "Main"
    SetOutPath ${{APP_DIR}}
    File /r "dist\\StockMonitor\\*.*"
    
    CreateDirectory "$$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortcut "$$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$${APP_EXECUTABLE}"
    CreateShortcut "$$DESKTOP\\${{APP_NAME}}.lnk" "$${APP_EXECUTABLE}"
SectionEnd

Section "Uninstall"
    Delete "$$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk"
    Delete "$$DESKTOP\\${{APP_NAME}}.lnk"
    RMDir "$$SMPROGRAMS\\${{APP_NAME}}"
    RMDir /r "$${APP_DIR}"
SectionEnd
"""
    
    def build_macos_installer(self):
        logger.info("Building macOS installer...")
        
        if not self.is_macos:
            logger.warning("Not on macOS, skipping macOS installer build")
            return True
        
        app_path = self.dist_dir / 'StockMonitor.app'
        if not app_path.exists():
            logger.error(f"App bundle not found: {app_path}")
            return False
        
        try:
            dmg_path = self.build_dir / 'macos' / 'StockMonitor.dmg'
            dmg_path.parent.mkdir(parents=True, exist_ok=True)
            
            subprocess.run(
                [
                    'hdiutil', 'create',
                    '-volname', 'StockMonitor',
                    '-srcfolder', str(app_path),
                    '-ov', '-format', 'UDZO',
                    str(dmg_path)
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"macOS DMG created: {dmg_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build macOS installer: {e}")
            return False
    
    def build(self, clean: bool = True, skip_deps: bool = False):
        logger.info("=" * 50)
        logger.info("Starting build process")
        logger.info("=" * 50)
        
        if clean:
            self.clean()
        
        self.prepare_resources()
        
        if not skip_deps:
            if not self.install_dependencies():
                logger.error("Failed to install dependencies")
                return False
            
            if not self.install_playwright_browsers():
                logger.warning("Failed to install Playwright browsers")
        
        if not self.build_with_pyinstaller():
            logger.error("PyInstaller build failed")
            return False
        
        if self.is_windows:
            self.build_windows_installer()
        elif self.is_macos:
            self.build_macos_installer()
        
        logger.info("=" * 50)
        logger.info("Build process completed successfully")
        logger.info("=" * 50)
        
        return True
    
    def build_debug(self):
        logger.info("Building in debug mode...")
        return self.build(clean=False, skip_deps=True)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Build StockMonitor native installer')
    parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation')
    parser.add_argument('--debug', action='store_true', help='Build in debug mode')
    
    args = parser.parse_args()
    
    builder = BuildManager()
    
    if args.debug:
        success = builder.build_debug()
    else:
        success = builder.build(clean=args.clean, skip_deps=args.skip_deps)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()