"""Alert prioritization and queue management utilities."""
from datetime import datetime, timedelta
from fraud_alert_system.database import Alert
import yaml
import os


def load_config():
    """Load configuration from config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if not os.path.exists(config_path):
        return {
            'sla_thresholds': {
                'CRITICAL': 15,
                'HIGH': 60,
                'MEDIUM': 240,
                'LOW': 1440
            },
            'priority_calculation': {
                'risk_score_weight': 0.6,
                'age_penalty_weight': 0.4,
                'max_priority_score': 100,
                'age_penalty_before_sla_max': 40,
                'age_penalty_after_sla_max': 60
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_config():
    """Get cached config or load it."""
    if not hasattr(get_config, '_config'):
        get_config._config = load_config()
    return get_config._config


def calculate_priority_score(alert):
    """
    Calculate priority score combining risk score and age.
    Higher score = higher priority.
    
    Formula: (Risk Score × 0.6) + (Age Penalty × 0.4)
    Age Penalty increases with time past SLA threshold.
    """
    config = get_config()
    priority_config = config.get('priority_calculation', {})
    sla_thresholds_config = config.get('sla_thresholds', {})
    
    risk_weight = priority_config.get('risk_score_weight', 0.6)
    age_weight = priority_config.get('age_penalty_weight', 0.4)
    max_score = priority_config.get('max_priority_score', 100)
    before_sla_max = priority_config.get('age_penalty_before_sla_max', 40)
    after_sla_max = priority_config.get('age_penalty_after_sla_max', 60)
    
    risk_component = alert.risk_score * risk_weight
    
    # SLA thresholds by severity (in minutes)
    sla_thresholds = {
        'CRITICAL': sla_thresholds_config.get('CRITICAL', 15),
        'HIGH': sla_thresholds_config.get('HIGH', 60),
        'MEDIUM': sla_thresholds_config.get('MEDIUM', 240),
        'LOW': sla_thresholds_config.get('LOW', 1440)
    }
    
    # Calculate age in minutes
    age_minutes = (datetime.utcnow() - alert.created_at).total_seconds() / 60
    sla_threshold = sla_thresholds.get(alert.severity, 1440)
    
    # Age penalty: 0-100 based on how far past SLA
    if age_minutes <= sla_threshold:
        age_penalty = (age_minutes / sla_threshold) * before_sla_max  # Max points before SLA
    else:
        # Past SLA: exponential penalty
        over_sla = age_minutes - sla_threshold
        age_penalty = before_sla_max + min(after_sla_max, (over_sla / sla_threshold) * after_sla_max)
    
    priority_score = risk_component + (age_penalty * age_weight)
    return min(max_score, priority_score)


def get_sla_status(alert):
    """Get SLA status for an alert."""
    config = get_config()
    sla_thresholds_config = config.get('sla_thresholds', {})
    
    sla_thresholds = {
        'CRITICAL': sla_thresholds_config.get('CRITICAL', 15),
        'HIGH': sla_thresholds_config.get('HIGH', 60),
        'MEDIUM': sla_thresholds_config.get('MEDIUM', 240),
        'LOW': sla_thresholds_config.get('LOW', 1440)
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
    config = get_config()
    sla_thresholds_config = config.get('sla_thresholds', {})
    
    sla_thresholds = {
        'CRITICAL': sla_thresholds_config.get('CRITICAL', 15),
        'HIGH': sla_thresholds_config.get('HIGH', 60),
        'MEDIUM': sla_thresholds_config.get('MEDIUM', 240),
        'LOW': sla_thresholds_config.get('LOW', 1440)
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

