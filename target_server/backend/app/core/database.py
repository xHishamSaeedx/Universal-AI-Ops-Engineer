from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create Base class for models
Base = declarative_base()

# Global variables for lazy initialization
_engine = None
_SessionLocal = None

def get_engine():
    """Get database engine with lazy initialization"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=settings.debug
        )
    return _engine

def get_session_local():
    """Get SessionLocal class with lazy initialization"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_db():
    """Dependency to get database session"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log the error but don't crash the app startup
        print(f"Warning: Could not create database tables: {e}")
        print("Database tables will be created when the database is available.")