"""Alert prioritization and queue management utilities."""
from datetime import datetime, timedelta
from fraud_alert_system.database import Alert


def calculate_priority_score(alert):
    """
    Calculate priority score combining risk score and age.
    Higher score = higher priority.
    
    Formula: (Risk Score × 0.6) + (Age Penalty × 0.4)
    Age Penalty increases with time past SLA threshold.
    """
    risk_component = alert.risk_score * 0.6
    
    # SLA thresholds by severity (in minutes)
    sla_thresholds = {
        'CRITICAL': 15,  # 15 minutes
        'HIGH': 60,      # 1 hour
        'MEDIUM': 240,   # 4 hours
        'LOW': 1440      # 24 hours
    }
    
    # Calculate age in minutes
    age_minutes = (datetime.utcnow() - alert.created_at).total_seconds() / 60
    sla_threshold = sla_thresholds.get(alert.severity, 1440)
    
    # Age penalty: 0-100 based on how far past SLA
    if age_minutes <= sla_threshold:
        age_penalty = (age_minutes / sla_threshold) * 40  # Max 40 points before SLA
    else:
        # Past SLA: exponential penalty
        over_sla = age_minutes - sla_threshold
        age_penalty = 40 + min(60, (over_sla / sla_threshold) * 60)
    
    priority_score = risk_component + (age_penalty * 0.4)
    return min(100, priority_score)


def get_sla_status(alert):
    """Get SLA status for an alert."""
    sla_thresholds = {
        'CRITICAL': 15,  # minutes
        'HIGH': 60,
        'MEDIUM': 240,
        'LOW': 1440
    }
    
    age_minutes = (datetime.utcnow() - alert.created_at).total_seconds() / 60
    sla_threshold = sla_thresholds.get(alert.severity, 1440)
    
    if age_minutes > sla_threshold:
        return 'PAST_SLA'
    elif age_minutes > sla_threshold * 0.8:
        return 'APPROACHING_SLA'
    else:
        return 'OK'


def get_time_to_sla(alert):
    """Get time remaining until SLA breach (in minutes)."""
    sla_thresholds = {
        'CRITICAL': 15,
        'HIGH': 60,
        'MEDIUM': 240,
        'LOW': 1440
    }
    
    age_minutes = (datetime.utcnow() - alert.created_at).total_seconds() / 60
    sla_threshold = sla_thresholds.get(alert.severity, 1440)
    
    remaining = sla_threshold - age_minutes
    return remaining


def sort_alerts_by_priority(alerts):
    """Sort alerts by priority score (highest first)."""
    alerts_with_priority = [(alert, calculate_priority_score(alert)) for alert in alerts]
    alerts_with_priority.sort(key=lambda x: x[1], reverse=True)
    return [alert for alert, _ in alerts_with_priority]

