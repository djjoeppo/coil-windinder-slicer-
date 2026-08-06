# main.pyw
import sys
from pathlib import Path

# Add application root directory to system path for correct module imports
app_root = Path(__file__).resolve().parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

# Import and execute the main entry point
from main import main

if __name__ == "__main__":
    main()
