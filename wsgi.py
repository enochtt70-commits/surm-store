# wsgi.py - PythonAnywhere WSGI entry point
import sys
import os

# Add the project directory to sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from app import create_app
application = create_app('production')
