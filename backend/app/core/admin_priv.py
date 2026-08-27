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

supabase_admin = create_client(url, key) if url and key else None  # type: ignore


def require_supabase_admin():
	"""Return the privileged client only when an admin provisioning action needs it."""
	if supabase_admin is None:
		raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables (checked backend/.env)")
	return supabase_admin
