#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oracle_db_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # If the developer runs `manage.py runserver` without specifying
    # an address/port, default to 192.168.18.55:8005 to be accessible on the local network
    # This respects any explicit addr:port the user provides.
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        # `runserver` may accept an optional second argument for addr:port.
        # When it's absent (i.e., only 'runserver' present), inject our default.
        if len(sys.argv) == 2:
            sys.argv.append('192.168.18.55:8005')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main() 