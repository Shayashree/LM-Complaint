import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.models.models import Role, User

@pytest.fixture(scope="function")
def db_session():
    # Use isolated memory database for unit testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Pre-populate roles for testing relations
    roles = [
        Role(name="SUPER_ADMIN", permissions=["*"]),
        Role(name="INSPECTOR", permissions=["scan", "verify"])
    ]
    for r in roles:
        session.add(r)
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
