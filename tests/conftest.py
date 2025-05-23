import sys
import os
import pytest

# Ensure the app/ directory is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
