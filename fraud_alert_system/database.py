"""Database schema and connection management."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Transaction(Base):
    """Transaction table schema."""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(50), nullable=False, index=True)
    merchant = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    transaction_date = Column(DateTime, nullable=False, index=True)
    card_type = Column(String(20))
    device_id = Column(String(50), index=True)
    ip_address = Column(String(45))
    country = Column(String(50))
    city = Column(String(100))
    mcc_code = Column(String(10))  # Merchant Category Code
    status = Column(String(20), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Alert table schema for fraud flags."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    transaction_id = Column(String(50), ForeignKey('transactions.transaction_id'), nullable=False)
    rule_triggered = Column(String(100), nullable=False)  # Which rule was triggered
    severity = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, default=0.0)  # 0-100
    status = Column(String(20), default='OPEN', index=True)  # OPEN, REVIEWING, ESCALATED, DISMISSED, RESOLVED
    analyst_id = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    
    transaction = relationship("Transaction")


class AuditLog(Base):
    """Audit log for all analyst actions."""
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(50), unique=True, nullable=False, index=True)
    alert_id = Column(String(50), ForeignKey('alerts.alert_id'), nullable=False)
    analyst_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # VIEWED, ESCALATED, DISMISSED, RESOLVED, NOTE_ADDED
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    alert = relationship("Alert")


def get_database_path():
    """Get the database file path."""
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'fraudops.db')


def create_database():
    """Create database and tables."""
    db_path = get_database_path()
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get database session."""
    db_path = get_database_path()
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

