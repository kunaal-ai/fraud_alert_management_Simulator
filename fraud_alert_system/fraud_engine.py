"""Rule-based fraud detection engine."""
from fraud_alert_system.database import get_session, Transaction, Alert
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid


class FraudDetectionEngine:
    """Fraud detection rules engine."""
    
    def __init__(self):
        self.session = get_session()
    
    def calculate_risk_score(self, rules_triggered):
        """Calculate overall risk score (0-100) based on triggered rules."""
        base_score = 0
        rule_weights = {
            'HIGH_AMOUNT': 30,
            'VELOCITY': 25,
            'GEO_JUMP': 20,
            'DEVICE_SHARING': 15,
            'UNUSUAL_TIME': 10,
            'SUSPICIOUS_MERCHANT': 15
        }
        
        for rule in rules_triggered:
            base_score += rule_weights.get(rule, 5)
        
        return min(100, base_score)
    
    def get_severity(self, risk_score):
        """Map risk score to severity level."""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def check_high_amount(self, transaction):
        """Rule: Transaction amount exceeds threshold."""
        threshold = 5000
        if transaction.amount > threshold:
            return True, f"Amount ${transaction.amount:,.2f} exceeds threshold ${threshold:,.2f}"
        return False, None
    
    def check_velocity(self, transaction):
        """Rule: Too many transactions in short time window."""
        time_window = timedelta(hours=1)
        start_time = transaction.transaction_date - time_window
        
        count = self.session.query(func.count(Transaction.id)).filter(
            and_(
                Transaction.customer_id == transaction.customer_id,
                Transaction.transaction_date >= start_time,
                Transaction.transaction_date <= transaction.transaction_date,
                Transaction.id != transaction.id
            )
        ).scalar()
        
        threshold = 5
        if count >= threshold:
            return True, f"Customer made {count + 1} transactions in the last hour"
        return False, None
    
    def check_geo_jump(self, transaction):
        """Rule: Geographic location jump (impossible travel)."""
        # Check for transactions in different locations within short time
        time_window = timedelta(hours=2)
        start_time = transaction.transaction_date - time_window
        
        recent_transactions = self.session.query(Transaction).filter(
            and_(
                Transaction.customer_id == transaction.customer_id,
                Transaction.transaction_date >= start_time,
                Transaction.transaction_date < transaction.transaction_date,
                Transaction.id != transaction.id
            )
        ).all()
        
        for recent_txn in recent_transactions:
            if recent_txn.city != transaction.city or recent_txn.country != transaction.country:
                return True, f"Location jump from {recent_txn.city}, {recent_txn.country} to {transaction.city}, {transaction.country} within {time_window.total_seconds()/3600:.1f} hours"
        
        return False, None
    
    def check_device_sharing(self, transaction):
        """Rule: Same device used by multiple customers (potential card sharing)."""
        # Count how many different customers used this device recently
        time_window = timedelta(days=7)
        start_time = transaction.transaction_date - time_window
        
        unique_customers = self.session.query(func.count(func.distinct(Transaction.customer_id))).filter(
            and_(
                Transaction.device_id == transaction.device_id,
                Transaction.transaction_date >= start_time,
                Transaction.transaction_date <= transaction.transaction_date
            )
        ).scalar()
        
        threshold = 3
        if unique_customers >= threshold:
            return True, f"Device {transaction.device_id} used by {unique_customers} different customers in the last 7 days"
        return False, None
    
    def check_unusual_time(self, transaction):
        """Rule: Transaction at unusual time (e.g., 2-5 AM)."""
        hour = transaction.transaction_date.hour
        # Flag transactions between 2 AM and 5 AM
        if 2 <= hour <= 5:
            return True, f"Transaction occurred at unusual time: {transaction.transaction_date.strftime('%H:%M')}"
        return False, None
    
    def check_suspicious_merchant(self, transaction):
        """Rule: Transaction at high-risk merchant category."""
        # High-risk MCC codes (gaming, adult entertainment, etc.)
        high_risk_mccs = ["7995", "7273", "5967", "5912"]  # Simplified list
        if transaction.mcc_code in high_risk_mccs:
            return True, f"Transaction at high-risk merchant category (MCC: {transaction.mcc_code})"
        return False, None
    
    def analyze_transaction(self, transaction):
        """Run all fraud detection rules on a transaction."""
        rules_triggered = []
        rule_details = []
        
        # Run all rules
        checks = [
            ('HIGH_AMOUNT', self.check_high_amount),
            ('VELOCITY', self.check_velocity),
            ('GEO_JUMP', self.check_geo_jump),
            ('DEVICE_SHARING', self.check_device_sharing),
            ('UNUSUAL_TIME', self.check_unusual_time),
            ('SUSPICIOUS_MERCHANT', self.check_suspicious_merchant)
        ]
        
        for rule_name, check_func in checks:
            triggered, detail = check_func(transaction)
            if triggered:
                rules_triggered.append(rule_name)
                rule_details.append(detail)
        
        return rules_triggered, rule_details
    
    def generate_alert(self, transaction, rules_triggered, rule_details):
        """Generate an alert for a suspicious transaction."""
        if not rules_triggered:
            return None
        
        risk_score = self.calculate_risk_score(rules_triggered)
        severity = self.get_severity(risk_score)
        
        alert_id = 'ALT' + str(uuid.uuid4()).replace('-', '').upper()[:12]
        
        alert = Alert(
            alert_id=alert_id,
            transaction_id=transaction.transaction_id,
            rule_triggered=', '.join(rules_triggered),
            severity=severity,
            risk_score=risk_score,
            status='OPEN',
            notes=' | '.join(rule_details)
        )
        
        self.session.add(alert)
        self.session.commit()
        
        return alert
    
    def process_transactions(self, limit=None):
        """Process transactions and generate alerts."""
        # Get transactions that don't have alerts yet
        query = self.session.query(Transaction).outerjoin(
            Alert, Transaction.transaction_id == Alert.transaction_id
        ).filter(Alert.id == None).order_by(Transaction.transaction_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        transactions = query.all()
        alerts_generated = 0
        
        print(f"Processing {len(transactions)} transactions...")
        
        for transaction in transactions:
            rules_triggered, rule_details = self.analyze_transaction(transaction)
            
            if rules_triggered:
                alert = self.generate_alert(transaction, rules_triggered, rule_details)
                if alert:
                    alerts_generated += 1
        
        print(f"✓ Generated {alerts_generated} new alerts")
        return alerts_generated
    
    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == '__main__':
    engine = FraudDetectionEngine()
    try:
        engine.process_transactions()
    finally:
        engine.close()

