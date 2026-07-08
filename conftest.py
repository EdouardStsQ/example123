import os
import sys

# make scripts/ importable as top-level modules in tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
