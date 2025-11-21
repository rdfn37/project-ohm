import google.auth

import os
from dotenv import load_dotenv

load_dotenv()

credentials, project = google.auth.default()

# If project is None from auth, fallback to env var
if not project:
    project = os.getenv("PROJECT_ID")

print(f"Active Project: {project}")

# If it's a service account, it has an email attribute
if hasattr(credentials, "service_account_email"):
    print(f"Identity: {credentials.service_account_email}")
else:
    print("Identity: User Credentials (ADC)")
    # For User Credentials, the email isn't always stored locally in the object,
    # but the 'project' above is the critical part for billing/resources.
