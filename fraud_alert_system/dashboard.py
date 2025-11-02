"""Streamlit dashboard for fraud alert management."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fraud_alert_system.database import get_session, Alert, Transaction, AuditLog, create_database
from fraud_alert_system.priority_manager import (
    calculate_priority_score, get_sla_status, get_time_to_sla, sort_alerts_by_priority
)
from fraud_alert_system.customer_profiles import get_customer_risk_profile
from fraud_alert_system.data_generator import generate_transactions, save_transactions_to_csv
from fraud_alert_system.ingestion import load_transactions_from_csv
from fraud_alert_system.fraud_engine import FraudDetectionEngine
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid
import os


# Custom CSS for professional styling
def load_custom_css():
    """Load custom CSS styling for professional appearance."""
    st.markdown("""
    <style>
        /* Main styling */
        .main {
            padding-top: 2rem;
        }
        
        /* Header styling */
        .header-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header-title {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1f2937;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 0.5rem;
        }
        
        /* Status badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-critical {
            background-color: #fee2e2;
            color: #991b1b;
        }
        
        .badge-high {
            background-color: #fef3c7;
            color: #92400e;
        }
        
        .badge-medium {
            background-color: #dbeafe;
            color: #1e40af;
        }
        
        .badge-low {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .badge-open {
            background-color: #fef3c7;
            color: #92400e;
        }
        
        .badge-resolved {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .badge-escalated {
            background-color: #fee2e2;
            color: #991b1b;
        }
        
        .badge-dismissed {
            background-color: #e5e7eb;
            color: #374151;
        }
        
        .badge-reviewing {
            background-color: #dbeafe;
            color: #1e40af;
        }
        
        /* SLA badges */
        .badge-sla-ok {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .badge-sla-warning {
            background-color: #fef3c7;
            color: #92400e;
        }
        
        .badge-sla-critical {
            background-color: #fee2e2;
            color: #991b1b;
        }
        
        /* Section containers */
        .section-container {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }
        
        /* Info boxes */
        .info-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .warning-box {
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .success-box {
            background: #f0fdf4;
            border-left: 4px solid #10b981;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* Table styling */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f9fafb;
        }
        
        /* Remove Streamlit default styling */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Typography */
        h1, h2, h3 {
            color: #1f2937;
            font-weight: 700;
        }
        
        /* Card hover effect */
        .hover-card {
            transition: all 0.3s ease;
        }
        
        .hover-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
    </style>
    """, unsafe_allow_html=True)


def get_severity_badge_html(severity):
    """Get HTML badge for severity."""
    badge_class = {
        'CRITICAL': 'badge-critical',
        'HIGH': 'badge-high',
        'MEDIUM': 'badge-medium',
        'LOW': 'badge-low'
    }.get(severity, 'badge')
    return f'<span class="badge {badge_class}">{severity}</span>'


def get_status_badge_html(status):
    """Get HTML badge for status."""
    badge_class = {
        'OPEN': 'badge-open',
        'RESOLVED': 'badge-resolved',
        'ESCALATED': 'badge-escalated',
        'DISMISSED': 'badge-dismissed',
        'REVIEWING': 'badge-reviewing'
    }.get(status, 'badge')
    return f'<span class="badge {badge_class}">{status}</span>'


def get_sla_badge_html(sla_status, time_to_sla):
    """Get HTML badge for SLA status."""
    if sla_status == 'PAST_SLA':
        return f'<span class="badge badge-sla-critical">🔴 Past SLA ({abs(int(time_to_sla))} min)</span>'
    elif sla_status == 'APPROACHING_SLA':
        return f'<span class="badge badge-sla-warning">🟡 {int(time_to_sla)} min to SLA</span>'
    else:
        return f'<span class="badge badge-sla-ok">🟢 OK ({int(time_to_sla)} min)</span>'


def log_audit_action(alert_id, analyst_id, action, details=None):
    """Log an analyst action to audit log."""
    session = get_session()
    try:
        log_entry = AuditLog(
            log_id='LOG' + str(uuid.uuid4()).replace('-', '').upper()[:12],
            alert_id=alert_id,
            analyst_id=analyst_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        st.error(f"Error logging action: {e}")
    finally:
        session.close()


def perform_bulk_action(session, alert_ids, action, analyst_id, details=""):
    """Perform bulk action on multiple alerts."""
    alerts = session.query(Alert).filter(Alert.alert_id.in_(alert_ids)).all()
    action_count = 0
    
    for alert in alerts:
        if action == "DISMISS":
            alert.status = 'DISMISSED'
            log_action = "DISMISSED"
        elif action == "RESOLVE":
            alert.status = 'RESOLVED'
            alert.resolved_at = datetime.utcnow()
            log_action = "RESOLVED"
        elif action == "ASSIGN":
            alert.analyst_id = analyst_id
            log_action = "ASSIGNED"
        
        alert.analyst_id = analyst_id
        session.commit()
        log_audit_action(alert.alert_id, analyst_id, log_action, 
                        f"Bulk action: {details}" if details else f"Bulk {action}")
        action_count += 1
    
    return action_count


# Default analyst credentials (simplified for demo)
ANALYST_CREDENTIALS = {
    "analyst1": {"password": "password123", "name": "Analyst 1", "id": "ANALYST001"},
    "analyst2": {"password": "password123", "name": "Analyst 2", "id": "ANALYST002"},
    "admin": {"password": "admin123", "name": "Admin User", "id": "ADMIN001"}
}


def authenticate_user(username, password):
    """Simple authentication check."""
    if username in ANALYST_CREDENTIALS:
        if ANALYST_CREDENTIALS[username]["password"] == password:
            return True, ANALYST_CREDENTIALS[username]
    return False, None


def initialize_sample_data_if_needed():
    """Initialize sample data if database is empty (for new deployments)."""
    session = get_session()
    try:
        # Check if database has any transactions
        transaction_count = session.query(Transaction).count()
        
        if transaction_count == 0:
            # Database is empty - generate sample data
            with st.spinner('🔄 Initializing sample data (first run only)...'):
                # Generate transactions
                df = generate_transactions(num_transactions=500, days_back=30)
                
                # Save to temporary CSV file
                temp_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                os.makedirs(temp_dir, exist_ok=True)
                csv_path = os.path.join(temp_dir, 'temp_transactions.csv')
                save_transactions_to_csv(df, csv_path)
                
                # Load transactions into database
                load_transactions_from_csv(csv_path)
                
                # Run fraud detection engine
                engine = FraudDetectionEngine()
                try:
                    alerts_generated = engine.process_transactions()
                    st.success(f'✅ Initialized database with {len(df)} transactions and {alerts_generated} alerts!')
                finally:
                    engine.close()
                
                # Clean up temp file
                if os.path.exists(csv_path):
                    os.remove(csv_path)
        # If transaction_count > 0, database already has data, skip initialization
    except Exception as e:
        # If initialization fails, log error but don't block the app
        st.warning(f'⚠️ Could not initialize sample data: {e}')
    finally:
        session.close()


def main():
    st.set_page_config(
        page_title="FraudOps Alert Management",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database - ensure tables exist (idempotent operation)
    # This is critical for Streamlit Cloud deployments where the database may not exist
    try:
        create_database()
    except Exception as e:
        st.error(f"❌ Error initializing database: {e}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    # Initialize sample data if database is empty (for new deployments)
    # Only runs once when database is first created
    if 'data_initialized' not in st.session_state:
        initialize_sample_data_if_needed()
        st.session_state.data_initialized = True
    
    # Load custom CSS
    load_custom_css()
    
    # Authentication check
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.analyst_info = None
    
    # Show login form if not authenticated
    if not st.session_state.authenticated:
        st.title("🔒 FraudOps Alert Management System")
        st.divider()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("🔐 Analyst Login")
            st.info("**Default credentials:**\n- Username: `analyst1` | Password: `password123`\n- Username: `admin` | Password: `admin123`")
            
            username = st.text_input("Username", key="login_username", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter password")
            
            col_login1, col_login2, col_login3 = st.columns([2, 1, 2])
            with col_login2:
                if st.button("Login", use_container_width=True, type="primary"):
                    success, analyst_info = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.analyst_info = analyst_info
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
        
        # Footer
        st.markdown("<hr>", unsafe_allow_html=True)
        st.caption("Fraud Alert Management Simulator | Portfolio Prototype by Kunaal | 2025")
        return
    
    # User is authenticated - show main dashboard
    analyst_info = st.session_state.analyst_info
    analyst_id = analyst_info["id"]
    
    # Identity Bar - Simple analyst selection in sidebar
    with st.sidebar:
        st.subheader("👤 Analyst Identity")
        
        # Map analyst info to display name
        analyst_display = f"{analyst_info['name']} ({analyst_id})"
        
        user = st.selectbox(
            "Logged in as:",
            [analyst_display],
            key="analyst_display"
        )
        st.success(f"Session active: {analyst_info['name']}")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.analyst_info = None
            st.rerun()
        
        st.divider()
        st.subheader("📊 View Mode")
        view_mode = st.radio(
            "Select View",
            ["Alert Queue", "Customer Profile"],
            key="view_mode",
            label_visibility="collapsed"
        )
        
        st.divider()
        st.subheader("🔍 Filters")
        
        status_filter = st.multiselect(
            "Alert Status",
            ["OPEN", "REVIEWING", "ESCALATED", "DISMISSED", "RESOLVED"],
            default=["OPEN", "REVIEWING"]
        )
        
        severity_filter = st.multiselect(
            "Severity Level",
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            default=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        )
        
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
        
        sort_option = st.selectbox(
            "Sort By",
            ["Priority (Highest First)", "Created Date (Newest)", "Risk Score (Highest)", "Created Date (Oldest)"],
            key="sort_option"
        )
        
        st.divider()
        st.caption("**Version:** 2.0.0")
        st.caption("**Last Updated:** " + datetime.now().strftime("%Y-%m-%d"))
    
    # Main content area - Title appears only once
    st.title("🔒 FraudOps Alert Management System")
    
    session = get_session()
    
    try:
        if view_mode == "Alert Queue":
            # Build query with loading spinner
            with st.spinner('Loading alerts...'):
                query = session.query(Alert).join(Transaction)
                
                if status_filter:
                    query = query.filter(Alert.status.in_(status_filter))
                
                if severity_filter:
                    query = query.filter(Alert.severity.in_(severity_filter))
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    query = query.filter(
                        and_(
                            Alert.created_at >= datetime.combine(start_date, datetime.min.time()),
                            Alert.created_at <= datetime.combine(end_date, datetime.max.time())
                        )
                    )
                
                alerts = query.all()
                
                # Sort alerts based on option
                if sort_option == "Priority (Highest First)":
                    alerts = sort_alerts_by_priority(alerts)
                elif sort_option == "Risk Score (Highest)":
                    alerts = sorted(alerts, key=lambda x: x.risk_score, reverse=True)
                elif sort_option == "Created Date (Newest)":
                    alerts = sorted(alerts, key=lambda x: x.created_at, reverse=True)
                elif sort_option == "Created Date (Oldest)":
                    alerts = sorted(alerts, key=lambda x: x.created_at)
                
                # Limit to realistic demo size (top 20)
                alerts = alerts[:20]
            
            st.success(f"Loaded {len(alerts)} alerts")
            
            st.divider()
            st.subheader("📈 Dashboard Overview")
            
            # Calculate metrics
            total_alerts = len(alerts)
            open_alerts = len([a for a in alerts if a.status == 'OPEN'])
            critical_alerts = len([a for a in alerts if a.severity == 'CRITICAL'])
            high_alerts = len([a for a in alerts if a.severity == 'HIGH'])
            medium_alerts = len([a for a in alerts if a.severity == 'MEDIUM'])
            low_alerts = len([a for a in alerts if a.severity == 'LOW'])
            escalated_alerts = len([a for a in alerts if a.status == 'ESCALATED'])
            past_sla = len([a for a in alerts if get_sla_status(a) == 'PAST_SLA' and a.status in ['OPEN', 'REVIEWING']])
            resolved_alerts = len([a for a in alerts if a.status == 'RESOLVED'])
            
            # Group 1: Overall Metrics
            st.markdown("#### Overall Status")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Alerts", f"{total_alerts:,}", delta=None)
            with col2:
                st.metric("Open Alerts", f"{open_alerts:,}", 
                         delta=f"-{total_alerts - open_alerts}" if total_alerts > open_alerts else None)
            with col3:
                st.metric("Resolved", f"{resolved_alerts:,}", delta=None)
            
            # Group 2: Severity Breakdown
            st.markdown("#### Severity Breakdown")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Critical", critical_alerts, 
                         delta="⚠️ Urgent" if critical_alerts > 0 else None,
                         delta_color="inverse" if critical_alerts > 0 else "normal")
            with col2:
                st.metric("High", high_alerts, delta=None)
            with col3:
                st.metric("Medium", medium_alerts, delta=None)
            with col4:
                st.metric("Low", low_alerts, delta=None)
            
            # Group 3: Action Required
            st.markdown("#### Action Required")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Escalated", escalated_alerts, delta=None)
            with col2:
                st.metric("Past SLA", past_sla, 
                         delta="🚨 Action Required" if past_sla > 0 else None,
                         delta_color="inverse" if past_sla > 0 else "normal")
            
            st.divider()
            
            # Bulk Operations Section
            if alerts:
                st.subheader("⚡ Bulk Operations")
                st.markdown('<div class="info-box">💡 <strong>Tip:</strong> Select multiple alerts below, then use bulk actions to process them efficiently.</div>', 
                          unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("✅ Resolve Selected", key="bulk_resolve", use_container_width=True):
                        if 'selected_alerts' in st.session_state and st.session_state.selected_alerts:
                            count = perform_bulk_action(session, st.session_state.selected_alerts, 
                                                       "RESOLVE", analyst_id, "Bulk resolve")
                            st.success(f"✅ Successfully resolved {count} alert(s)!")
                            st.session_state.selected_alerts = []
                            st.rerun()
                        else:
                            st.warning("Please select at least one alert first.")
                
                with col2:
                    if st.button("❌ Dismiss Selected", key="bulk_dismiss", use_container_width=True):
                        if 'selected_alerts' in st.session_state and st.session_state.selected_alerts:
                            count = perform_bulk_action(session, st.session_state.selected_alerts, 
                                                       "DISMISS", analyst_id, "Bulk dismiss as false positive")
                            st.success(f"❌ Successfully dismissed {count} alert(s) as false positives!")
                            st.session_state.selected_alerts = []
                            st.rerun()
                        else:
                            st.warning("Please select at least one alert first.")
                
                with col3:
                    if 'selected_alerts' in st.session_state and st.session_state.selected_alerts:
                        st.info(f"📌 **{len(st.session_state.selected_alerts)}** alert(s) selected")
            
            st.divider()
            
            # Alert list - Minimal core columns
            if not alerts:
                st.info("ℹ️ No alerts found matching the current filters. Try adjusting your filter criteria.")
            else:
                st.subheader(f"🚨 Alert Queue ({len(alerts)} alerts)")
                st.caption(f"Sorted by: {sort_option}")
                
                # Initialize selected alerts in session state
                if 'selected_alerts' not in st.session_state:
                    st.session_state.selected_alerts = []
                
                # Multi-select for bulk operations
                alert_options = {f"{a.alert_id} | {a.severity} | Risk: {a.risk_score:.1f}": a.alert_id 
                                for a in alerts}
                selected_alert_labels = st.multiselect(
                    "Select alerts for bulk operations:",
                    options=list(alert_options.keys()),
                    default=[label for label in alert_options.keys() 
                             if alert_options[label] in st.session_state.selected_alerts],
                    key="bulk_select"
                )
                st.session_state.selected_alerts = [alert_options[label] for label in selected_alert_labels]
                
                # Minimal core columns only
                alert_data = []
                for alert in alerts:
                    sla_status = get_sla_status(alert)
                    priority_score = calculate_priority_score(alert)
                    time_to_sla = get_time_to_sla(alert)
                    
                    # Format SLA indicator (simplified)
                    if sla_status == 'PAST_SLA':
                        sla_indicator = "🔴 Past SLA"
                    elif sla_status == 'APPROACHING_SLA':
                        sla_indicator = "🟡 Warning"
                    else:
                        sla_indicator = "🟢 OK"
                    
                    alert_data.append({
                        'Alert ID': alert.alert_id,
                        'Severity': alert.severity,
                        'Risk Score': f"{alert.risk_score:.1f}",
                        'Priority': f"{priority_score:.1f}",
                        'SLA': sla_indicator,
                        'Status': alert.status,
                        'Created': alert.created_at.strftime('%Y-%m-%d %H:%M')
                    })
                
                df_alerts = pd.DataFrame(alert_data)
                
                # Display minimal table
                st.dataframe(df_alerts, use_container_width=True, hide_index=True, height=300)
                
                st.divider()
                
                # Alert detail view with expandable panels
                st.subheader("🔍 Alert Investigation")
                
                alert_ids = [a.alert_id for a in alerts]
                selected_alert_id = st.selectbox(
                    "Select Alert to View Details:",
                    alert_ids,
                    key="alert_selector"
                )
                
                if selected_alert_id:
                    with st.spinner('Loading alert details...'):
                        alert = session.query(Alert).filter(Alert.alert_id == selected_alert_id).first()
                    
                    if alert:
                        # Log view action
                        log_audit_action(selected_alert_id, analyst_id, "VIEWED", "Alert details viewed")
                        
                        # Quick action buttons at top
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if st.button("🚨 Escalate", key="escalate", use_container_width=True):
                                with st.spinner('Escalating alert...'):
                                    alert.status = 'ESCALATED'
                                    alert.analyst_id = analyst_id
                                    session.commit()
                                    log_audit_action(selected_alert_id, analyst_id, "ESCALATED", "Alert escalated")
                                st.success("✅ Alert escalated successfully!")
                                st.rerun()
                        
                        with col2:
                            if st.button("✅ Resolve", key="resolve", use_container_width=True):
                                with st.spinner('Resolving alert...'):
                                    alert.status = 'RESOLVED'
                                    alert.resolved_at = datetime.utcnow()
                                    alert.analyst_id = analyst_id
                                    session.commit()
                                    log_audit_action(selected_alert_id, analyst_id, "RESOLVED", "Alert resolved")
                                st.success("✅ Alert resolved successfully!")
                                st.rerun()
                        
                        with col3:
                            if st.button("❌ Dismiss", key="dismiss", use_container_width=True):
                                with st.spinner('Dismissing alert...'):
                                    alert.status = 'DISMISSED'
                                    alert.analyst_id = analyst_id
                                    session.commit()
                                    log_audit_action(selected_alert_id, analyst_id, "DISMISSED", "Alert dismissed as false positive")
                                st.success("✅ Alert dismissed successfully!")
                                st.rerun()
                        
                        with col4:
                            if st.button("📝 Reviewing", key="reviewing", use_container_width=True):
                                with st.spinner('Updating status...'):
                                    alert.status = 'REVIEWING'
                                    alert.analyst_id = analyst_id
                                    session.commit()
                                    log_audit_action(selected_alert_id, analyst_id, "REVIEWING", "Alert set to reviewing status")
                                st.success("✅ Alert status updated!")
                                st.rerun()
                        
                        # Expandable panels for details
                        with st.expander("📋 View Full Alert Details", expanded=False):
                            col1, col2 = st.columns(2)
                        
                            with col1:
                                priority_score = calculate_priority_score(alert)
                                sla_status = get_sla_status(alert)
                                time_to_sla = get_time_to_sla(alert)
                                
                                st.markdown(f"**Alert ID:** `{alert.alert_id}`")
                                st.markdown(f"**Severity:** {get_severity_badge_html(alert.severity)}", unsafe_allow_html=True)
                                st.markdown(f"**Risk Score:** {alert.risk_score:.1f} / 100")
                                st.markdown(f"**Priority Score:** {priority_score:.1f} / 100")
                                st.markdown(f"**SLA Status:** {get_sla_badge_html(sla_status, time_to_sla)}", unsafe_allow_html=True)
                                
                                if time_to_sla < 0:
                                    st.markdown(f"**Time Past SLA:** {abs(int(time_to_sla))} minutes")
                                else:
                                    st.markdown(f"**Time to SLA:** {int(time_to_sla)} minutes")
                                
                                st.markdown(f"**Status:** {get_status_badge_html(alert.status)}", unsafe_allow_html=True)
                                st.markdown(f"**Rule Triggered:** `{alert.rule_triggered}`")
                                st.markdown(f"**Created:** {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                                st.markdown(f"**Age:** {(datetime.utcnow() - alert.created_at).total_seconds() / 60:.0f} minutes")
                            
                            # Get transaction details
                            transaction = session.query(Transaction).filter(
                                Transaction.transaction_id == alert.transaction_id
                            ).first()
                            
                            with col2:
                                if transaction:
                                    st.markdown(f"**Transaction ID:** `{transaction.transaction_id}`")
                                    st.markdown(f"**Customer ID:** `{transaction.customer_id}`")
                                    st.markdown(f"**Merchant:** {transaction.merchant}")
                                    st.markdown(f"**Amount:** ${transaction.amount:,.2f}")
                                    st.markdown(f"**Date:** {transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
                                    st.markdown(f"**Location:** {transaction.city}, {transaction.country}")
                                    st.markdown(f"**Device ID:** `{transaction.device_id}`")
                                    st.markdown(f"**IP Address:** `{transaction.ip_address}`")
                                    st.markdown(f"**MCC Code:** `{transaction.mcc_code}`")
                                    
                                    if st.button("👤 View Customer Profile", key="view_customer", use_container_width=True):
                                        st.session_state.customer_id_to_view = transaction.customer_id
                                        st.session_state.view_mode = "Customer Profile"
                                        st.rerun()
                        
                        # Notes in expandable panel
                        with st.expander("📝 View Alert Notes & Actions", expanded=False):
                            st.markdown("**Alert Notes:**")
                            st.info(alert.notes or "*No notes available for this alert.*")
                            
                            st.divider()
                            st.markdown("**Add Note:**")
                            new_note = st.text_area("Enter your notes here:", key="note_input", height=100,
                                                  placeholder="Type your investigation notes, findings, or actions taken...")
                            if st.button("💾 Save Note", key="save_note", use_container_width=True):
                                if new_note.strip():
                                    with st.spinner('Saving note...'):
                                        if alert.notes:
                                            alert.notes = alert.notes + "\n\n" + f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {new_note}"
                                        else:
                                            alert.notes = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {new_note}"
                                        session.commit()
                                        log_audit_action(selected_alert_id, analyst_id, "NOTE_ADDED", new_note)
                                    st.success("✅ Note saved successfully!")
                                    st.rerun()
                                else:
                                    st.warning("Please enter a note before saving.")
                        
                        # Audit trail in expandable panel
                        with st.expander("📜 View Audit Trail", expanded=False):
                            audit_logs = session.query(AuditLog).filter(
                                AuditLog.alert_id == selected_alert_id
                            ).order_by(AuditLog.timestamp.desc()).all()
                            
                            if audit_logs:
                                log_data = []
                                for log in audit_logs:
                                    log_data.append({
                                        'Timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                        'Analyst': log.analyst_id,
                                        'Action': log.action,
                                        'Details': log.details or '-'
                                    })
                                st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
                            else:
                                st.info("No audit log entries for this alert.")
            
            # Compact Charts Section
            st.divider()
            st.subheader("📊 Analytics Dashboard")
            
            if alerts:
                # Prepare data for charts
                alert_df = pd.DataFrame([{
                    'alert_id': a.alert_id,
                    'severity': a.severity,
                    'status': a.status,
                    'risk_score': a.risk_score,
                    'created_at': a.created_at,
                    'transaction_id': a.transaction_id
                } for a in alerts])
                
                # Get merchant information for each alert
                merchant_data = []
                for alert in alerts:
                    transaction = session.query(Transaction).filter(
                        Transaction.transaction_id == alert.transaction_id
                    ).first()
                    if transaction:
                        merchant_data.append({
                            'merchant': transaction.merchant,
                            'alert_id': alert.alert_id
                        })
                
                merchant_df = pd.DataFrame(merchant_data) if merchant_data else pd.DataFrame()
                
                # Row 1: Severity Pie Chart and Status Chart
                col1, col2 = st.columns(2)
                
                with col1:
                    if not alert_df.empty:
                        st.markdown("#### Alerts by Severity")
                        severity_counts = alert_df['severity'].value_counts()
                        # Create pie chart with professional colors
                        fig_severity = px.pie(
                            values=severity_counts.values,
                            names=severity_counts.index,
                            color_discrete_sequence=['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],  # Red, Orange, Blue, Green
                            hole=0.3
                        )
                        fig_severity.update_layout(
                            showlegend=True,
                            font=dict(color='#1e293b', size=12),
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                        st.plotly_chart(fig_severity, use_container_width=True)
                        st.caption("**Distribution by Severity Level**")
                
                with col2:
                    if not alert_df.empty:
                        st.markdown("#### Alerts by Status")
                        status_counts = alert_df['status'].value_counts()
                        status_df = pd.DataFrame({
                            'Status': status_counts.index,
                            'Count': status_counts.values
                        })
                        st.bar_chart(status_df.set_index('Status'))
                        st.caption("**Distribution by Status**")
                
                # Row 2: Top Risky Merchants (Horizontal Bar) and Time Chart
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    if not merchant_df.empty:
                        st.markdown("#### Top Risky Merchants")
                        merchant_counts = merchant_df['merchant'].value_counts().head(10)
                        # Create horizontal bar chart
                        merchant_df_chart = pd.DataFrame({
                            'Merchant': merchant_counts.index,
                            'Alert Count': merchant_counts.values
                        })
                        # Sort for horizontal display (largest at top)
                        merchant_df_chart = merchant_df_chart.sort_values('Alert Count', ascending=True)
                        
                        # Use plotly for horizontal bar chart
                        fig_merchants = go.Figure(go.Bar(
                            x=merchant_df_chart['Alert Count'],
                            y=merchant_df_chart['Merchant'],
                            orientation='h',
                            marker_color='#1e3a8a'
                        ))
                        fig_merchants.update_layout(
                            xaxis_title="Alert Count",
                            yaxis_title="",
                            height=300,
                            font=dict(color='#1e293b', size=11),
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                        st.plotly_chart(fig_merchants, use_container_width=True)
                        st.caption("**Top 10 Merchants by Alert Count**")
                    else:
                        st.info("No merchant data available.")
                
                with col2:
                    if not alert_df.empty:
                        st.markdown("#### Alerts Over Time")
                        alert_df['date'] = pd.to_datetime(alert_df['created_at']).dt.date
                        daily_counts = alert_df.groupby('date').size()
                        daily_df = pd.DataFrame({
                            'Date': daily_counts.index,
                            'Alert Count': daily_counts.values
                        })
                        # Use plotly for better line chart
                        fig_time = px.line(
                            daily_df,
                            x='Date',
                            y='Alert Count',
                            markers=True,
                            color_discrete_sequence=['#1e3a8a']
                        )
                        fig_time.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Alert Count",
                            height=300,
                            font=dict(color='#1e293b', size=11),
                            margin=dict(l=0, r=0, t=0, b=0),
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_time, use_container_width=True)
                        st.caption("**Daily Alert Trends**")
            else:
                st.info("No alerts available for analytics.")
        
        elif view_mode == "Customer Profile":
            st.divider()
            st.subheader("👤 Customer Risk Profile & Investigation")
            
            # Get customer ID input
            customer_id_input = st.text_input(
                "**Enter Customer ID:**",
                value=st.session_state.get('customer_id_to_view', ''),
                key="customer_id_input",
                placeholder="e.g., CUST12345678"
            )
            
            if customer_id_input:
                try:
                    profile = get_customer_risk_profile(customer_id_input, session)
                    
                    # Summary metrics
                    st.markdown("#### 📊 Risk Overview")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Alerts", profile['total_alerts'])
                    with col2:
                        st.metric("Avg Risk Score", f"{profile['avg_risk_score']:.1f}")
                    with col3:
                        st.metric("Max Risk Score", f"{profile['max_risk_score']:.1f}")
                    with col4:
                        st.metric("Total Transactions", profile['total_transactions'])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Alert breakdown
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📈 Alerts by Severity")
                        severity_df = pd.DataFrame({
                            'Severity': list(profile['severity_counts'].keys()),
                            'Count': list(profile['severity_counts'].values())
                        })
                        st.bar_chart(severity_df.set_index('Severity'))
                    
                    with col2:
                        st.markdown("#### 📊 Alerts by Status")
                        status_df = pd.DataFrame({
                            'Status': list(profile['status_counts'].keys()),
                            'Count': list(profile['status_counts'].values())
                        })
                        st.bar_chart(status_df.set_index('Status'))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Transaction statistics
                    st.markdown("#### 💰 Transaction Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Amount", f"${profile['total_amount']:,.2f}")
                    with col2:
                        st.metric("Avg Transaction", f"${profile['avg_amount']:,.2f}")
                    with col3:
                        st.metric("Max Transaction", f"${profile['max_amount']:,.2f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Recent Activity (7 days)", f"{profile['recent_count']} transactions")
                    with col2:
                        st.metric("Recent Amount (7 days)", f"${profile['recent_amount']:,.2f}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Pattern indicators
                    st.markdown("#### 🔍 Pattern Indicators")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Unique Locations", profile['unique_locations'])
                    with col2:
                        st.metric("Unique Devices", profile['unique_devices'])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Recent alerts
                    if profile['alerts']:
                        st.markdown(f"#### 🚨 Recent Alerts (showing {len(profile['alerts'])} of {profile['total_alerts']})")
                        alert_data = []
                        for alert in profile['alerts']:
                            alert_data.append({
                                'Alert ID': alert.alert_id,
                                'Severity': alert.severity,
                                'Risk Score': f"{alert.risk_score:.1f}",
                                'Status': alert.status,
                                'Created': alert.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            })
                        st.dataframe(pd.DataFrame(alert_data), use_container_width=True, hide_index=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Recent transactions
                    if profile['transactions']:
                        st.markdown(f"#### 💳 Recent Transactions (showing {len(profile['transactions'])} of {profile['total_transactions']})")
                        txn_data = []
                        for txn in profile['transactions']:
                            txn_data.append({
                                'Transaction ID': txn.transaction_id,
                                'Merchant': txn.merchant,
                                'Amount': f"${txn.amount:,.2f}",
                                'Date': txn.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'Location': f"{txn.city}, {txn.country}",
                                'Device': txn.device_id
                            })
                        st.dataframe(pd.DataFrame(txn_data), use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"❌ Error loading customer profile: {e}")
                    st.info("ℹ️ Customer not found. Please check the Customer ID and try again.")
    
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        session.close()
    
    # Footer with branding
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Fraud Alert Management Simulator | Portfolio Prototype by Kunaal | 2025")


if __name__ == '__main__':
    main()
