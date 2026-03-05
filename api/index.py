import sys
import os

# Add the project root to the PYTHONPATH so Absolute imports from phase4 to phase3 etc work on Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase4.backend.main import app

# Vercel's serverless builder (@vercel/python) will look for an `app` object in api/index.py.
# The FastAPI app is natively compatible!
