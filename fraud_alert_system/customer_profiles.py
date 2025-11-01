"""Customer risk profile and investigation context utilities."""
from fraud_alert_system.database import get_session, Transaction, Alert
from datetime import datetime, timedelta
from sqlalchemy import func


def get_customer_risk_profile(customer_id, session):
    """
    Get comprehensive risk profile for a customer.
    Returns aggregated risk information.
    """
    # Get all transactions for this customer
    transactions = session.query(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Transaction.transaction_date.desc()).all()
    
    # Get all alerts for this customer
    alerts = session.query(Alert).join(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Alert.created_at.desc()).all()
    
    # Calculate aggregated risk score
    if alerts:
        avg_risk_score = sum(a.risk_score for a in alerts) / len(alerts)
        max_risk_score = max(a.risk_score for a in alerts)
    else:
        avg_risk_score = 0
        max_risk_score = 0
    
    # Get alert counts by severity
    severity_counts = {
        'CRITICAL': len([a for a in alerts if a.severity == 'CRITICAL']),
        'HIGH': len([a for a in alerts if a.severity == 'HIGH']),
        'MEDIUM': len([a for a in alerts if a.severity == 'MEDIUM']),
        'LOW': len([a for a in alerts if a.severity == 'LOW'])
    }
    
    # Get alert counts by status
    status_counts = {
        'OPEN': len([a for a in alerts if a.status == 'OPEN']),
        'RESOLVED': len([a for a in alerts if a.status == 'RESOLVED']),
        'DISMISSED': len([a for a in alerts if a.status == 'DISMISSED']),
        'ESCALATED': len([a for a in alerts if a.status == 'ESCALATED'])
    }
    
    # Transaction statistics
    if transactions:
        total_amount = sum(t.amount for t in transactions)
        avg_amount = total_amount / len(transactions)
        max_amount = max(t.amount for t in transactions)
        
        # Recent activity (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_transactions = [t for t in transactions if t.transaction_date >= recent_date]
        recent_count = len(recent_transactions)
        recent_amount = sum(t.amount for t in recent_transactions)
    else:
        total_amount = 0
        avg_amount = 0
        max_amount = 0
        recent_count = 0
        recent_amount = 0
    
    # Unique locations
    unique_locations = len(set((t.city, t.country) for t in transactions if t.city))
    
    # Unique devices
    unique_devices = len(set(t.device_id for t in transactions if t.device_id))
    
    return {
        'customer_id': customer_id,
        'total_transactions': len(transactions),
        'total_alerts': len(alerts),
        'avg_risk_score': round(avg_risk_score, 1),
        'max_risk_score': round(max_risk_score, 1),
        'severity_counts': severity_counts,
        'status_counts': status_counts,
        'total_amount': round(total_amount, 2),
        'avg_amount': round(avg_amount, 2),
        'max_amount': round(max_amount, 2),
        'recent_count': recent_count,
        'recent_amount': round(recent_amount, 2),
        'unique_locations': unique_locations,
        'unique_devices': unique_devices,
        'alerts': alerts[:10],  # Last 10 alerts
        'transactions': transactions[:20]  # Last 20 transactions
    }


def get_customer_transactions(customer_id, session, limit=50):
    """Get transaction history for a customer."""
    return session.query(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Transaction.transaction_date.desc()).limit(limit).all()


def get_customer_alerts(customer_id, session):
    """Get all alerts for a customer."""
    return session.query(Alert).join(Transaction).filter(
        Transaction.customer_id == customer_id
    ).order_by(Alert.created_at.desc()).all()

