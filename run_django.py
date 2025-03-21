import os
import sys
import site

# Add virtual environment site-packages to path
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Lib', 'site-packages')
site.addsitedir(venv_path)
sys.path.insert(0, venv_path)

# Now import Django components
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    # Set Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")
    
    # Run Django's runserver command
    execute_from_command_line(["manage.py", "runserver"]) 