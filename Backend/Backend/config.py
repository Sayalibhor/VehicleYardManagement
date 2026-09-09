import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "vyms-super-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'yard_management.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SAP Integration Settings
    SAP_CPI_ENDPOINT = os.environ.get("SAP_CPI_ENDPOINT", "https://mock-cpi.internal/sap/yard-events")
    SAP_AUTH_TOKEN = os.environ.get("SAP_AUTH_TOKEN", "Basic VEVTVF9VU0VSOlBBU1NXT1JE")
    SAP_MAX_RETRIES = 3
    SAP_MOCK_MODE = True  # Emulates CPI 200 OK responses locally