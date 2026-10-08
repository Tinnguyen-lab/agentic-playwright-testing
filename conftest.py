"""Pytest bootstrap: đảm bảo `import src...` chạy được từ gốc repo (Windows-safe)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
