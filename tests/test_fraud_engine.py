"""Unit tests for fraud detection engine."""
import pytest
from fraud_alert_system.database import create_database, get_session, Transaction, Alert
from fraud_alert_system.fraud_engine import FraudDetectionEngine
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_transaction(db_session):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        transaction_id='TEST_TXN_001',
        customer_id='TEST_CUST_001',
        merchant='Test Merchant',
        amount=100.00,
        currency='USD',
        transaction_date=datetime.now(),
        card_type='Visa',
        device_id='TEST_DEVICE_001',
        ip_address='192.168.1.1',
        country='USA',
        city='New York',
        mcc_code='5411',
        status='completed'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


def test_high_amount_rule():
    """Test high amount fraud rule."""
    engine = FraudDetectionEngine()
    
    # Create a high-value transaction
    transaction = Transaction(
        transaction_id='HIGH_AMT_TXN',
        customer_id='CUST_001',
        merchant='Merchant',
        amount=6000.00,  # Above $5000 threshold
        currency='USD',
        transaction_date=datetime.now(),
        card_type='Visa',
        device_id='DEV_001',
        ip_address='1.1.1.1',
        country='USA',
        city='NYC',
        mcc_code='5411'
    )
    
    triggered, detail = engine.check_high_amount(transaction)
    assert triggered is True
    assert "exceeds threshold" in detail.lower()
    
    # Test normal amount
    transaction.amount = 100.00
    triggered, detail = engine.check_high_amount(transaction)
    assert triggered is False
    
    engine.close()


def test_unusual_time_rule():
    """Test unusual time fraud rule."""
    engine = FraudDetectionEngine()
    
    # Transaction at 3 AM
    transaction = Transaction(
        transaction_id='TIME_TXN',
        customer_id='CUST_001',
        merchant='Merchant',
        amount=100.00,
        currency='USD',
        transaction_date=datetime.now().replace(hour=3, minute=0),
        card_type='Visa',
        device_id='DEV_001',
        ip_address='1.1.1.1',
        country='USA',
        city='NYC',
        mcc_code='5411'
    )
    
    triggered, detail = engine.check_unusual_time(transaction)
    assert triggered is True
    
    # Normal time transaction
    transaction.transaction_date = datetime.now().replace(hour=14, minute=0)
    triggered, detail = engine.check_unusual_time(transaction)
    assert triggered is False
    
    engine.close()


def test_risk_score_calculation():
    """Test risk score calculation."""
    engine = FraudDetectionEngine()
    
    # Single rule triggered
    score = engine.calculate_risk_score(['HIGH_AMOUNT'])
    assert 0 < score <= 100
    
    # Multiple rules triggered
    score = engine.calculate_risk_score(['HIGH_AMOUNT', 'VELOCITY', 'GEO_JUMP'])
    assert score >= 50  # Should be higher with multiple rules
    
    # Risk score should cap at 100
    score = engine.calculate_risk_score(['HIGH_AMOUNT', 'VELOCITY', 'GEO_JUMP', 'DEVICE_SHARING', 'UNUSUAL_TIME', 'SUSPICIOUS_MERCHANT'])
    assert score <= 100
    
    engine.close()


def test_severity_mapping():
    """Test severity level mapping from risk score."""
    engine = FraudDetectionEngine()
    
    assert engine.get_severity(90) == 'CRITICAL'
    assert engine.get_severity(70) == 'HIGH'
    assert engine.get_severity(50) == 'MEDIUM'
    assert engine.get_severity(30) == 'LOW'
    
    engine.close()


def test_alert_generation(db_session, sample_transaction):
    """Test alert generation."""
    engine = FraudDetectionEngine()
    
    # Create a transaction that should trigger high amount rule
    high_amount_txn = Transaction(
        transaction_id='ALERT_TEST_TXN',
        customer_id='CUST_002',
        merchant='Merchant',
        amount=8000.00,
        currency='USD',
        transaction_date=datetime.now(),
        card_type='Visa',
        device_id='DEV_002',
        ip_address='1.1.1.1',
        country='USA',
        city='NYC',
        mcc_code='5411'
    )
    
    db_session.add(high_amount_txn)
    db_session.commit()
    
    rules_triggered, rule_details = engine.analyze_transaction(high_amount_txn)
    
    if rules_triggered:
        alert = engine.generate_alert(high_amount_txn, rules_triggered, rule_details)
        assert alert is not None
        assert alert.transaction_id == high_amount_txn.transaction_id
        assert alert.severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0 <= alert.risk_score <= 100
    
    engine.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

