#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# -------------------------------------------------------------------------
# AUTO-CREATE SUPERUSER (Only for SQLite Demo)
# -------------------------------------------------------------------------
# This creates a user: 
# Username: admin
# Password: password123
# Email: admin@example.com
echo "Creating default superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'password123')"