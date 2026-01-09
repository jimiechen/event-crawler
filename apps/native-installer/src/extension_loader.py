#!/usr/bin/env python3
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


class ExtensionLoader:
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.os_type = platform.system()
        self.is_windows = self.os_type == 'Windows'
        self.is_macos = self.os_type == 'Darwin'
        self.is_linux = self.os_type == 'Linux'
        
        self.extension_id = None
        self.manifest = None
        
        logger.info(f"ExtensionLoader initialized with path: {self.extension_path}")
    
    def validate_extension(self) -> bool:
        logger.info("Validating Chrome extension...")
        
        manifest_path = self.extension_path / 'manifest.json'
        if not manifest_path.exists():
            logger.error(f"manifest.json not found in: {self.extension_path}")
            return False
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
            
            required_fields = ['name', 'version', 'manifest_version']
            for field in required_fields:
                if field not in self.manifest:
                    logger.error(f"Required field '{field}' not found in manifest")
                    return False
            
            self.extension_id = self._generate_extension_id()
            logger.info(f"Extension validated successfully: {self.manifest.get('name')} v{self.manifest.get('version')}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse manifest.json: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating extension: {e}")
            return False
    
    def _generate_extension_id(self) -> str:
        if 'key' in self.manifest:
            try:
                import hashlib
                key = self.manifest['key']
                hash_obj = hashlib.sha256(key.encode('utf-8'))
                extension_id = ''.join([chr(ord('a') + int(b, 16) % 26) for b in hash_obj.hexdigest()[:32]])
                return extension_id
            except Exception as e:
                logger.warning(f"Failed to generate extension ID from key: {e}")
        
        return 'abcdefghijklmnopabcdefghijklmnop'
    
    def get_chrome_executable_path(self) -> Optional[Path]:
        logger.info("Locating Chrome executable...")
        
        possible_paths = []
        
        if self.is_windows:
            possible_paths = [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
                Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
            ]
        elif self.is_macos:
            possible_paths = [
                Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                Path('/Applications/Chromium.app/Contents/MacOS/Chromium'),
            ]
        else:
            possible_paths = [
                Path('/usr/bin/google-chrome'),
                Path('/usr/bin/chromium-browser'),
                Path('/usr/bin/chromium'),
                Path('/snap/bin/chromium'),
            ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found Chrome at: {path}")
                return path
        
        logger.warning("Chrome executable not found")
        return None
    
    def get_chrome_user_data_dir(self) -> Optional[Path]:
        logger.info("Locating Chrome user data directory...")
        
        if self.is_windows:
            user_data_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / 'Google' / 'Chrome' / 'User Data'
        elif self.is_macos:
            user_data_dir = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
        else:
            user_data_dir = Path.home() / '.config' / 'google-chrome'
        
        if user_data_dir.exists():
            logger.info(f"Found Chrome user data directory: {user_data_dir}")
            return user_data_dir
        
        logger.warning("Chrome user data directory not found")
        return None
    
    def install_extension_via_chrome(self) -> bool:
        logger.info("Installing extension via Chrome...")
        
        chrome_path = self.get_chrome_executable_path()
        if not chrome_path:
            logger.error("Chrome executable not found")
            return False
        
        user_data_dir = self.get_chrome_user_data_dir()
        if not user_data_dir:
            logger.warning("Chrome user data directory not found, using temporary directory")
            user_data_dir = Path.home() / '.stockmonitor' / 'chrome-user-data'
            user_data_dir.mkdir(parents=True, exist_ok=True)
        
        args = [
            str(chrome_path),
            f'--load-extension={self.extension_path}',
            f'--user-data-dir={user_data_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-networking',
            '--disable-sync',
            '--metrics-recording-only',
        ]
        
        try:
            logger.info(f"Starting Chrome with extension: {' '.join(args)}")
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Chrome started with extension loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to start Chrome: {e}")
            return False
    
    def create_native_messaging_manifest(self, host_name: str = 'com.stockmonitor.native') -> bool:
        logger.info(f"Creating native messaging manifest for: {host_name}")
        
        if not self.is_windows and not self.is_macos and not self.is_linux:
            logger.warning(f"Native messaging not supported on {self.os_type}")
            return False
        
        manifest_content = {
            'name': host_name,
            'description': 'StockMonitor Native Messaging Host',
            'path': self._get_native_host_path(),
            'type': 'stdio',
            'allowed_origins': [
                f'chrome-extension://{self.extension_id}/*',
            ]
        }
        
        manifest_dir = self._get_native_messaging_dir()
        if not manifest_dir:
            logger.error("Failed to determine native messaging directory")
            return False
        
        try:
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / f'{host_name}.json'
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_content, f, indent=2)
            
            logger.info(f"Native messaging manifest created: {manifest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create native messaging manifest: {e}")
            return False
    
    def _get_native_messaging_dir(self) -> Optional[Path]:
        if self.is_windows:
            return Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / 'Google' / 'Chrome' / 'User Data' / 'NativeMessagingHosts'
        elif self.is_macos:
            return Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'NativeMessagingHosts'
        elif self.is_linux:
            return Path.home() / '.config' / 'google-chrome' / 'NativeMessagingHosts'
        return None
    
    def _get_native_host_path(self) -> str:
        if self.is_windows:
            return str(Path(__file__).parent.parent / 'StockMonitor.exe')
        elif self.is_macos:
            return str(Path(__file__).parent.parent / 'StockMonitor.app' / 'Contents' / 'MacOS' / 'StockMonitor')
        else:
            return str(Path(__file__).parent.parent / 'StockMonitor')
    
    def copy_extension_to_resources(self, source_path: str) -> bool:
        logger.info(f"Copying extension from {source_path} to {self.extension_path}")
        
        source = Path(source_path)
        if not source.exists():
            logger.error(f"Source extension path not found: {source_path}")
            return False
        
        try:
            if self.extension_path.exists():
                shutil.rmtree(self.extension_path)
            
            shutil.copytree(source, self.extension_path)
            logger.info(f"Extension copied successfully to: {self.extension_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy extension: {e}")
            return False
    
    def get_extension_info(self) -> Dict[str, Any]:
        if not self.manifest:
            if not self.validate_extension():
                return {}
        
        return {
            'name': self.manifest.get('name'),
            'version': self.manifest.get('version'),
            'description': self.manifest.get('description', ''),
            'manifest_version': self.manifest.get('manifest_version'),
            'permissions': self.manifest.get('permissions', []),
            'host_permissions': self.manifest.get('host_permissions', []),
            'background': self.manifest.get('background'),
            'content_scripts': self.manifest.get('content_scripts', []),
            'path': str(self.extension_path),
            'id': self.extension_id,
        }
    
    def check_extension_compatibility(self) -> bool:
        logger.info("Checking extension compatibility...")
        
        if not self.manifest:
            if not self.validate_extension():
                return False
        
        manifest_version = self.manifest.get('manifest_version')
        
        if manifest_version == 3:
            logger.info("Extension uses Manifest V3 (recommended)")
        elif manifest_version == 2:
            logger.warning("Extension uses Manifest V2 (deprecated)")
        else:
            logger.error(f"Unsupported manifest version: {manifest_version}")
            return False
        
        permissions = self.manifest.get('permissions', [])
        required_permissions = ['nativeMessaging']
        
        for perm in required_permissions:
            if perm not in permissions:
                logger.warning(f"Extension missing required permission: {perm}")
        
        return True
    
    def prepare_extension_for_packaging(self) -> bool:
        logger.info("Preparing extension for packaging...")
        
        if not self.validate_extension():
            return False
        
        if not self.check_extension_compatibility():
            logger.warning("Extension compatibility check failed, continuing anyway...")
        
        return True