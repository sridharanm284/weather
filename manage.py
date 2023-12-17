#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading  # Import the threading module for concurrency

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forecast_server.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Start a thread to run the send_emails management command concurrently with runserver
    if 'runserver' in sys.argv:
        from subscription.management.commands.send_emails import Command  
        email_thread = threading.Thread(target=Command().handle)
        email_thread.daemon = True
        email_thread.start()

    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
