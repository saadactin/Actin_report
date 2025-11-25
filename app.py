#!/usr/bin/env python
"""
Django application entry point.
Run this file with: python app.py
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oracle_db_project.settings')
    
    # Setup Django
    django.setup()
    
    # Default to runserver on port 8007 if no arguments provided
    if len(sys.argv) == 1:
        sys.argv = ['manage.py', 'runserver', '127.0.0.1:8007']
    else:
        # If arguments are provided, prepend 'manage.py'
        sys.argv = ['manage.py'] + sys.argv[1:]
    
    # Execute the Django management command
    execute_from_command_line(sys.argv)

