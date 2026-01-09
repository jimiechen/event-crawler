#!/usr/bin/env python3
import os
import sys
import subprocess
import winreg
from pathlib import Path
from loguru import logger


class WindowsSetup:
    def __init__(self):
        self.app_name = "StockMonitor"
        self.app_version = "1.0.0"
        self.publisher = "StockMonitor Team"
        
        self.program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        self.program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        self.local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        self.app_data = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        
        self.install_dir = Path(self.program_files) / self.app_name
        self.start_menu_dir = Path(self.app_data) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / self.app_name
        self.desktop_dir = Path(os.path.expanduser('~\\Desktop'))
        
        self._setup_logging()
    
    def _setup_logging(self):
        log_dir = Path(self.local_app_data) / self.app_name / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / 'setup.log'
        logger.add(
            log_file,
            rotation='10 MB',
            retention='7 days',
            level='INFO',
            format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
        )
        logger.info("Windows Setup initialized")
    
    def check_admin_privileges(self) -> bool:
        logger.info("Checking admin privileges...")
        
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        if is_admin:
            logger.info("Admin privileges confirmed")
            return True
        else:
            logger.warning("Admin privileges not available")
            return False
    
    def request_admin_privileges(self):
        logger.info("Requesting admin privileges...")
        
        import ctypes
        import sys
        
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.info("Restarting with admin privileges...")
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)
        except Exception as e:
            logger.error(f"Failed to request admin privileges: {e}")
    
    def create_install_directory(self):
        logger.info(f"Creating install directory: {self.install_dir}")
        
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Install directory created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create install directory: {e}")
            return False
    
    def create_shortcuts(self):
        logger.info("Creating shortcuts...")
        
        try:
            self.start_menu_dir.mkdir(parents=True, exist_ok=True)
            
            exe_path = self.install_dir / 'StockMonitor.exe'
            
            if exe_path.exists():
                import pythoncom
                from win32com.shell import shell, shellcon
                
                start_menu_shortcut = self.start_menu_dir / f'{self.app_name}.lnk'
                desktop_shortcut = self.desktop_dir / f'{self.app_name}.lnk'
                
                shortcut = pythoncom.CoCreateInstance(
                    shell.CLSID_ShellLink,
                    None,
                    pythoncom.CLSCTX_INPROC_SERVER,
                    shell.IID_IShellLink
                )
                
                shortcut.SetPath(str(exe_path))
                shortcut.SetDescription(f"{self.app_name} - Stock Monitoring Application")
                shortcut.SetIconLocation(str(exe_path), 0)
                
                persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                
                persist_file.Save(str(start_menu_shortcut), 0)
                logger.info(f"Start menu shortcut created: {start_menu_shortcut}")
                
                persist_file.Save(str(desktop_shortcut), 0)
                logger.info(f"Desktop shortcut created: {desktop_shortcut}")
                
                return True
            else:
                logger.error(f"Executable not found: {exe_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create shortcuts: {e}")
            return False
    
    def register_uninstall(self):
        logger.info("Registering uninstall information...")
        
        try:
            uninstall_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                0,
                winreg.KEY_ALL_ACCESS
            )
            
            app_key = winreg.CreateKey(uninstall_key, self.app_name)
            
            winreg.SetValueEx(app_key, "DisplayName", 0, winreg.REG_SZ, self.app_name)
            winreg.SetValueEx(app_key, "DisplayVersion", 0, winreg.REG_SZ, self.app_version)
            winreg.SetValueEx(app_key, "Publisher", 0, winreg.REG_SZ, self.publisher)
            winreg.SetValueEx(app_key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
            winreg.SetValueEx(app_key, "UninstallString", 0, winreg.REG_SZ, f'"{self.install_dir}\\uninstall.exe"')
            
            winreg.CloseKey(app_key)
            winreg.CloseKey(uninstall_key)
            
            logger.info("Uninstall information registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register uninstall: {e}")
            return False
    
    def register_file_associations(self):
        logger.info("Registering file associations...")
        
        try:
            extensions = ['.csv', '.json']
            
            for ext in extensions:
                prog_id = f'{self.app_name}.{ext[1:]}'
                
                try:
                    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ext)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, prog_id)
                    winreg.CloseKey(key)
                    
                    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, prog_id)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{self.app_name} File")
                    winreg.CloseKey(key)
                    
                    icon_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{prog_id}\\DefaultIcon")
                    winreg.SetValueEx(icon_key, "", 0, winreg.REG_SZ, f'"{self.install_dir}\\StockMonitor.exe",0')
                    winreg.CloseKey(icon_key)
                    
                    command_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{prog_id}\\shell\\open\\command")
                    winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{self.install_dir}\\StockMonitor.exe" "%1"')
                    winreg.CloseKey(command_key)
                    
                    logger.info(f"Registered file association: {ext}")
                    
                except Exception as e:
                    logger.error(f"Failed to register {ext}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register file associations: {e}")
            return False
    
    def add_firewall_exception(self):
        logger.info("Adding firewall exception...")
        
        try:
            exe_path = self.install_dir / 'StockMonitor.exe'
            
            if exe_path.exists():
                subprocess.run(
                    [
                        'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                        f'name="{self.app_name}"',
                        f'dir=in',
                        'action=allow',
                        f'program="{exe_path}"',
                        'enable=yes'
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                logger.info("Firewall exception added successfully")
                return True
            else:
                logger.warning(f"Executable not found: {exe_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add firewall exception: {e}")
            return False
    
    def create_uninstaller(self):
        logger.info("Creating uninstaller...")
        
        try:
            uninstaller_script = f"""
import os
import shutil
import sys
from pathlib import Path

install_dir = Path(r"{self.install_dir}")
start_menu_dir = Path(r"{self.start_menu_dir}")
desktop_dir = Path(r"{self.desktop_dir}")

print("Uninstalling StockMonitor...")

try:
    # Remove shortcuts
    start_menu_shortcut = start_menu_dir / '{self.app_name}.lnk'
    desktop_shortcut = desktop_dir / '{self.app_name}.lnk'
    
    if start_menu_shortcut.exists():
        start_menu_shortcut.unlink()
        print(f"Removed: {{start_menu_shortcut}}")
    
    if desktop_shortcut.exists():
        desktop_shortcut.unlink()
        print(f"Removed: {{desktop_shortcut}}")
    
    # Remove start menu directory if empty
    if start_menu_dir.exists() and not list(start_menu_dir.iterdir()):
        start_menu_dir.rmdir()
        print(f"Removed: {{start_menu_dir}}")
    
    # Remove install directory
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print(f"Removed: {{install_dir}}")
    
    print("Uninstall completed successfully")
    
except Exception as e:
    print(f"Error during uninstall: {{e}}")
    sys.exit(1)
"""
            
            uninstaller_path = self.install_dir / 'uninstall.py'
            with open(uninstaller_path, 'w', encoding='utf-8') as f:
                f.write(uninstaller_script)
            
            logger.info(f"Uninstaller created: {uninstaller_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create uninstaller: {e}")
            return False
    
    def setup(self):
        logger.info("=" * 50)
        logger.info("Starting Windows Setup")
        logger.info("=" * 50)
        
        if not self.check_admin_privileges():
            logger.warning("Admin privileges required, requesting...")
            self.request_admin_privileges()
            return
        
        steps = [
            ("Creating install directory", self.create_install_directory),
            ("Creating shortcuts", self.create_shortcuts),
            ("Registering uninstall", self.register_uninstall),
            ("Registering file associations", self.register_file_associations),
            ("Adding firewall exception", self.add_firewall_exception),
            ("Creating uninstaller", self.create_uninstaller),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")
        
        logger.info("=" * 50)
        logger.info("Windows Setup completed successfully")
        logger.info("=" * 50)
        
        return True


def main():
    setup = WindowsSetup()
    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()