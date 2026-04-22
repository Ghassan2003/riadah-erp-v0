# Locust configuration for ERP System Load Testing
# This file is used as a reference config only.
# The actual test scenarios are in locust_erp.py

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
django.setup()
