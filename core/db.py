from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./performance_results.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()


# Database model
class PerformanceResult(Base):
    __tablename__ = "performance_results"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    lower_bound = Column(Integer, index=True)
    upper_bound = Column(Integer, index=True)
    processing_mode = Column(String, index=True)
    execution_time = Column(Float)
    cpu_time = Column(Float)
    memory_usage = Column(Float)
    cpu_utilization = Column(Float)
    result_value = Column(Float)
    cores_used = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PerformanceResult(id={self.id}, mode={self.processing_mode}, time={self.execution_time})>"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)


def get_db_stats():
    """Get database statistics"""
    db = SessionLocal()
    try:
        total_records = db.query(PerformanceResult).count()
        modes = db.query(PerformanceResult.processing_mode).distinct().all()
        return {
            "total_records": total_records,
            "processing_modes": [mode[0] for mode in modes]
        }
    finally:
        db.close()
