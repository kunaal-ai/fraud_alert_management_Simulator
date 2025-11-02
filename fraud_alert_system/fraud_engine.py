"""Rule-based fraud detection engine."""
from fraud_alert_system.database import get_session, Transaction, Alert
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid
import yaml
import os


def load_config():
    """Load configuration from config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return {
            'rules': {
                'high_amount': {'threshold': 5000, 'enabled': True},
                'velocity': {'threshold': 5, 'time_window_hours': 1, 'enabled': True},
                'geo_jump': {'time_window_hours': 2, 'enabled': True},
                'device_sharing': {'threshold': 3, 'time_window_days': 7, 'enabled': True},
                'unusual_time': {'start_hour': 2, 'end_hour': 5, 'enabled': True},
                'suspicious_merchant': {'high_risk_mcc_codes': ['7995', '7273', '5967', '5912'], 'enabled': True}
            },
            'rule_weights': {
                'HIGH_AMOUNT': 30,
                'VELOCITY': 25,
                'GEO_JUMP': 20,
                'DEVICE_SHARING': 15,
                'UNUSUAL_TIME': 10,
                'SUSPICIOUS_MERCHANT': 15,
                'DEFAULT': 5
            },
            'severity_thresholds': {
                'CRITICAL': 80,
                'HIGH': 60,
                'MEDIUM': 40,
                'LOW': 0
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class FraudDetectionEngine:
    """Fraud detection rules engine."""
    
    def __init__(self):
        self.session = get_session()
        self.config = load_config()
    
    def calculate_risk_score(self, rules_triggered):
        """Calculate overall risk score (0-100) based on triggered rules."""
        base_score = 0
        rule_weights = self.config.get('rule_weights', {})
        default_weight = rule_weights.get('DEFAULT', 5)
        
        for rule in rules_triggered:
            base_score += rule_weights.get(rule, default_weight)
        
        return min(100, base_score)
    
    def get_severity(self, risk_score):
        """Map risk score to severity level."""
        thresholds = self.config.get('severity_thresholds', {})
        critical = thresholds.get('CRITICAL', 80)
        high = thresholds.get('HIGH', 60)
        medium = thresholds.get('MEDIUM', 40)
        
        if risk_score >= critical:
            return 'CRITICAL'
        elif risk_score >= high:
            return 'HIGH'
        elif risk_score >= medium:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def check_high_amount(self, transaction):
        """Rule: Transaction amount exceeds threshold."""
        rule_config = self.config.get('rules', {}).get('high_amount', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        threshold = rule_config.get('threshold', 5000)
        if transaction.amount > threshold:
            return True, f"Amount ${transaction.amount:,.2f} exceeds threshold ${threshold:,.2f}"
        return False, None
    
    def check_velocity(self, transaction):
        """Rule: Too many transactions in short time window."""
        rule_config = self.config.get('rules', {}).get('velocity', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        time_window_hours = rule_config.get('time_window_hours', 1)
        time_window = timedelta(hours=time_window_hours)
        start_time = transaction.transaction_date - time_window
        
        count = self.session.query(func.count(Transaction.id)).filter(
            and_(
                Transaction.customer_id == transaction.customer_id,
                Transaction.transaction_date >= start_time,
                Transaction.transaction_date <= transaction.transaction_date,
                Transaction.id != transaction.id
            )
        ).scalar()
        
        threshold = rule_config.get('threshold', 5)
        if count >= threshold:
            return True, f"Customer made {count + 1} transactions in the last {time_window_hours} hour(s)"
        return False, None
    
    def check_geo_jump(self, transaction):
        """Rule: Geographic location jump (impossible travel)."""
        rule_config = self.config.get('rules', {}).get('geo_jump', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        # Check for transactions in different locations within short time
        time_window_hours = rule_config.get('time_window_hours', 2)
        time_window = timedelta(hours=time_window_hours)
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
        rule_config = self.config.get('rules', {}).get('device_sharing', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        # Count how many different customers used this device recently
        time_window_days = rule_config.get('time_window_days', 7)
        time_window = timedelta(days=time_window_days)
        start_time = transaction.transaction_date - time_window
        
        unique_customers = self.session.query(func.count(func.distinct(Transaction.customer_id))).filter(
            and_(
                Transaction.device_id == transaction.device_id,
                Transaction.transaction_date >= start_time,
                Transaction.transaction_date <= transaction.transaction_date
            )
        ).scalar()
        
        threshold = rule_config.get('threshold', 3)
        if unique_customers >= threshold:
            return True, f"Device {transaction.device_id} used by {unique_customers} different customers in the last {time_window_days} days"
        return False, None
    
    def check_unusual_time(self, transaction):
        """Rule: Transaction at unusual time (e.g., 2-5 AM)."""
        rule_config = self.config.get('rules', {}).get('unusual_time', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        hour = transaction.transaction_date.hour
        start_hour = rule_config.get('start_hour', 2)
        end_hour = rule_config.get('end_hour', 5)
        
        # Flag transactions within the unusual time window
        if start_hour <= hour <= end_hour:
            return True, f"Transaction occurred at unusual time: {transaction.transaction_date.strftime('%H:%M')}"
        return False, None
    
    def check_suspicious_merchant(self, transaction):
        """Rule: Transaction at high-risk merchant category."""
        rule_config = self.config.get('rules', {}).get('suspicious_merchant', {})
        if not rule_config.get('enabled', True):
            return False, None
        
        # High-risk MCC codes from config
        high_risk_mccs = rule_config.get('high_risk_mcc_codes', ["7995", "7273", "5967", "5912"])
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

