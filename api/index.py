import os
import sys

# Add project root and backend to sys.path so talent_platform can be loaded
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from talent_platform import create_app

app = create_app()
