#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path
from loguru import logger


class MacOSSetup:
    def __init__(self):
        self.app_name = "StockMonitor"
        self.app_version = "1.0.0"
        self.bundle_id = "com.stockmonitor.app"
        
        self.applications_dir = Path('/Applications')
        self.app_path = self.applications_dir / f'{self.app_name}.app'
        self.support_dir = Path.home() / 'Library' / 'Application Support' / self.app_name
        self.logs_dir = self.support_dir / 'logs'
        self.config_dir = self.support_dir / 'config'
        
        self._setup_logging()
    
    def _setup_logging(self):
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.logs_dir / 'setup.log'
        logger.add(
            log_file,
            rotation='10 MB',
            retention='7 days',
            level='INFO',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
        )
        logger.info("macOS Setup initialized")
    
    def check_permissions(self) -> bool:
        logger.info("Checking permissions...")
        
        try:
            test_file = Path('/tmp/stockmonitor_test')
            test_file.touch()
            test_file.unlink()
            logger.info("Permissions OK")
            return True
        except Exception as e:
            logger.error(f"Insufficient permissions: {e}")
            return False
    
    def create_support_directories(self):
        logger.info("Creating support directories...")
        
        try:
            self.support_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Support directories created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create support directories: {e}")
            return False
    
    def install_app_bundle(self, source_path: str) -> bool:
        logger.info(f"Installing app bundle from: {source_path}")
        
        source = Path(source_path)
        
        if not source.exists():
            logger.error(f"Source app bundle not found: {source}")
            return False
        
        try:
            if self.app_path.exists():
                logger.info(f"Removing existing app: {self.app_path}")
                shutil.rmtree(self.app_path)
            
            shutil.copytree(source, self.app_path)
            logger.info(f"App bundle installed to: {self.app_path}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to install app bundle: {e}")
            return False
    
    def set_permissions(self):
        logger.info("Setting permissions...")
        
        try:
            subprocess.run(
                ['chmod', '-R', '755', str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            subprocess.run(
                ['chown', '-R', f'{os.getuid()}:staff', str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Permissions set successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set permissions: {e}")
            return False
    
    def register_launch_services(self):
        logger.info("Registering with Launch Services...")
        
        try:
            subprocess.run(
                ['/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister',
                 '-v', str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Launch Services registration completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to register with Launch Services: {e}")
            return False
    
    def create_dock_icon(self):
        logger.info("Creating Dock icon...")
        
        try:
            dock_script = f"""
tell application "System Events"
    if not (exists process "Dock") then
        tell application "Dock" to activate
    end if
end tell

tell application "Dock"
    make new item at end with properties {path:"{self.app_path}", kind:file}
end tell
"""
            
            script_path = self.support_dir / 'add_to_dock.scpt'
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(dock_script)
            
            subprocess.run(
                ['osascript', str(script_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Dock icon created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create Dock icon: {e}")
            return False
    
    def configure_firewall(self):
        logger.info("Configuring firewall...")
        
        try:
            subprocess.run(
                ['/usr/libexec/ApplicationFirewall/socketfilterfw',
                 '--add', str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            subprocess.run(
                ['/usr/libexec/ApplicationFirewall/socketfilterfw',
                 '--unblockapp', str(self.app_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Firewall configured successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure firewall: {e}")
            return False
    
    def create_launch_agent(self):
        logger.info("Creating Launch Agent...")
        
        try:
            launch_agent_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.stockmonitor.launcher</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{self.app_path}/Contents/MacOS/StockMonitor</string>
    </array>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>{self.logs_dir}/launcher.log</string>
    
    <key>StandardErrorPath</key>
    <string>{self.logs_dir}/launcher_error.log</string>
    
    <key>WorkingDirectory</key>
    <string>{self.support_dir}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>STOCKMONITOR_HOME</key>
        <string>{self.support_dir}</string>
    </dict>
</dict>
</plist>
"""
            
            launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            launch_agent_path = launch_agents_dir / 'com.stockmonitor.launcher.plist'
            
            with open(launch_agent_path, 'w', encoding='utf-8') as f:
                f.write(launch_agent_plist)
            
            logger.info(f"Launch Agent created: {launch_agent_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Launch Agent: {e}")
            return False
    
    def create_uninstaller(self):
        logger.info("Creating uninstaller...")
        
        try:
            uninstaller_script = f"""#!/bin/bash

APP_NAME="{self.app_name}"
APP_PATH="{self.app_path}"
SUPPORT_DIR="{self.support_dir}"
LAUNCH_AGENT_PATH="{Path.home()}/Library/LaunchAgents/com.stockmonitor.launcher.plist"

echo "Uninstalling $APP_NAME..."

# Stop Launch Agent if running
if [ -f "$LAUNCH_AGENT_PATH" ]; then
    launchctl unload "$LAUNCH_AGENT_PATH" 2>/dev/null || true
    rm "$LAUNCH_AGENT_PATH"
    echo "Removed Launch Agent"
fi

# Remove app bundle
if [ -d "$APP_PATH" ]; then
    rm -rf "$APP_PATH"
    echo "Removed app bundle"
fi

# Remove support directory
if [ -d "$SUPPORT_DIR" ]; then
    rm -rf "$SUPPORT_DIR"
    echo "Removed support directory"
fi

echo "Uninstall completed successfully"
"""
            
            uninstaller_path = self.support_dir / 'uninstall.sh'
            with open(uninstaller_path, 'w', encoding='utf-8') as f:
                f.write(uninstaller_script)
            
            os.chmod(uninstaller_path, 0o755)
            
            logger.info(f"Uninstaller created: {uninstaller_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create uninstaller: {e}")
            return False
    
    def setup(self, source_path: str):
        logger.info("=" * 50)
        logger.info("Starting macOS Setup")
        logger.info("=" * 50)
        
        if not self.check_permissions():
            logger.error("Insufficient permissions")
            return False
        
        steps = [
            ("Creating support directories", self.create_support_directories),
            ("Installing app bundle", lambda: self.install_app_bundle(source_path)),
            ("Setting permissions", self.set_permissions),
            ("Registering Launch Services", self.register_launch_services),
            ("Creating Launch Agent", self.create_launch_agent),
            ("Creating uninstaller", self.create_uninstaller),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")
        
        logger.info("=" * 50)
        logger.info("macOS Setup completed successfully")
        logger.info("=" * 50)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup StockMonitor on macOS')
    parser.add_argument('source', help='Path to the app bundle (.app)')
    parser.add_argument('--dock', action='store_true', help='Add to Dock')
    parser.add_argument('--firewall', action='store_true', help='Configure firewall')
    
    args = parser.parse_args()
    
    setup = MacOSSetup()
    success = setup.setup(args.source)
    
    if success:
        if args.dock:
            setup.create_dock_icon()
        if args.firewall:
            setup.configure_firewall()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()