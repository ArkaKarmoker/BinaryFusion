#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Migrate database
python manage.py migrate

# 4. Create Superuser (Hardcoded)
# Since we don't have an env file, we set the password right here.
echo "Checking for superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# --- HARDCODED ADMIN DETAILS ---
USERNAME = 'admin'
EMAIL = 'binaryfusion.trade@outlook.com'
PASSWORD = 'Arka19052001@Karmoker'  # <--- CHANGE THIS PASSWORD HERE
# -------------------------------

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"Superuser '{USERNAME}' created successfully.")
else:
    print(f"Superuser '{USERNAME}' already exists. Skipping.")
EOF