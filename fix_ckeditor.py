import os
import sys
import site
import django

# Add virtual environment site-packages to path
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Lib', 'site-packages')
site.addsitedir(venv_path)
sys.path.insert(0, venv_path)

# Try to import ckeditor
try:
    import ckeditor
    print(f"CKEditor found at: {ckeditor.__file__}")
except ImportError as e:
    print(f"Failed to import ckeditor: {e}")

# Print Python path
print("Python path:")
for path in sys.path:
    print(f"  {path}")

# Print installed packages
print("\nInstalled packages in the virtual environment:")
try:
    import pkg_resources
    for pkg in pkg_resources.working_set:
        print(f"  {pkg.project_name} {pkg.version}")
except Exception as e:
    print(f"Error listing packages: {e}") 