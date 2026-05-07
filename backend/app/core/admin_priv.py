# backend/supabase_admin.py
import os
from supabase import create_client
from dotenv import load_dotenv

# Load the .env file that lives in the backend folder (ensure variables are available
# even when this module is imported from the project root)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

# This file ONLY lives on the backend
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
	raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables (checked backend/.env)")

# Initialize the Admin Client
supabase_admin = create_client(url, key)  # type: ignore
