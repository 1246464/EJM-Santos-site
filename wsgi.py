"""
WSGI entry point for production server (Gunicorn)
"""
from application import app

if __name__ == "__main__":
    app.run()
