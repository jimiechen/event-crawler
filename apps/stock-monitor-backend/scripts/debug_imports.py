
import sys
import os

sys.path.insert(0, os.getcwd())

try:
    print("Importing app.api.main...")
    from app.api import main
    print("Import app.api.main success")
except Exception as e:
    print(f"Error importing app.api.main: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Importing app.api.mcp_controller...")
    from app.api import mcp_controller
    print("Import app.api.mcp_controller success")
except Exception as e:
    print(f"Error importing app.api.mcp_controller: {e}")
    import traceback
    traceback.print_exc()
