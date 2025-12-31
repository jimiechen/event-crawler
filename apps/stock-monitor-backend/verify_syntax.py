import compileall
import os
import sys

def check_syntax(directory):
    print(f"Checking syntax for files in {directory}...")
    try:
        # compile_dir returns True if success, False if error
        # quiet=0 means print output to stdout
        if compileall.compile_dir(directory, quiet=0, force=True):
            print("✅ Syntax check passed.")
            return True
        else:
            print("❌ Syntax check failed.")
            return False
    except Exception as e:
        print(f"❌ Error during syntax check: {e}")
        return False

if __name__ == "__main__":
    target_dir = os.path.join(os.getcwd(), "app")
    if not check_syntax(target_dir):
        sys.exit(1)
