"""Streamlit dashboard for fraud alert management."""
import streamlit as st
import pandas as pd
from fraud_alert_system.database import get_session, Alert, Transaction, AuditLog
from fraud_alert_system.priority_manager import (
    calculate_priority_score, get_sla_status, get_time_to_sla, sort_alerts_by_priority
)
from fraud_alert_system.customer_profiles import get_customer_risk_profile
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid


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


def main():
    st.set_page_config(
        page_title="FraudOps Alert Management",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Professional Header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🔒 FraudOps Alert Management System</h1>
        <p class="header-subtitle">Enterprise Fraud Detection & Alert Triage Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for analyst login and filters
    with st.sidebar:
        st.markdown("### 👤 Analyst Portal")
        analyst_id = st.text_input("Analyst ID", value="ANALYST001", key="analyst_id", 
                                   help="Enter your analyst identification")
        
        st.markdown("---")
        st.markdown("### 📊 View Mode")
        view_mode = st.radio(
            "Select View",
            ["Alert Queue", "Customer Profile"],
            key="view_mode",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        
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
        
        st.markdown("---")
        st.markdown("**Version:** 2.0.0")
        st.markdown("**Last Updated:** " + datetime.now().strftime("%Y-%m-%d"))
    
    # Main content area
    session = get_session()
    
    try:
        if view_mode == "Alert Queue":
            # Build query
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
            
            # Professional Summary Metrics
            st.markdown("### 📈 Dashboard Overview")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            total_alerts = len(alerts)
            open_alerts = len([a for a in alerts if a.status == 'OPEN'])
            critical_alerts = len([a for a in alerts if a.severity == 'CRITICAL'])
            escalated_alerts = len([a for a in alerts if a.status == 'ESCALATED'])
            past_sla = len([a for a in alerts if get_sla_status(a) == 'PAST_SLA' and a.status in ['OPEN', 'REVIEWING']])
            
            with col1:
                st.metric("Total Alerts", f"{total_alerts:,}", delta=None)
            with col2:
                st.metric("Open Alerts", f"{open_alerts:,}", 
                         delta=f"-{total_alerts - open_alerts}" if total_alerts > open_alerts else None)
            with col3:
                st.metric("Critical", critical_alerts, 
                         delta="⚠️ Urgent" if critical_alerts > 0 else None,
                         delta_color="inverse" if critical_alerts > 0 else "normal")
            with col4:
                st.metric("Escalated", escalated_alerts, delta=None)
            with col5:
                st.metric("Past SLA", past_sla, 
                         delta="🚨 Action Required" if past_sla > 0 else None,
                         delta_color="inverse" if past_sla > 0 else "normal")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bulk Operations Section
            if alerts:
                st.markdown("### ⚡ Bulk Operations")
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
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Alert list
            if not alerts:
                st.markdown('<div class="info-box">ℹ️ No alerts found matching the current filters. Try adjusting your filter criteria.</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f"### 🚨 Alert Queue ({len(alerts):,} alerts) - *Sorted by {sort_option}*")
                
                # Initialize selected alerts in session state
                if 'selected_alerts' not in st.session_state:
                    st.session_state.selected_alerts = []
                
                # Multi-select for bulk operations
                alert_options = {f"{a.alert_id} | {a.severity} | Risk: {a.risk_score:.1f}": a.alert_id 
                                for a in alerts}
                selected_alert_labels = st.multiselect(
                    "**Select alerts for bulk operations:**",
                    options=list(alert_options.keys()),
                    default=[label for label in alert_options.keys() 
                             if alert_options[label] in st.session_state.selected_alerts],
                    key="bulk_select"
                )
                st.session_state.selected_alerts = [alert_options[label] for label in selected_alert_labels]
                
                # Display alerts in a styled table
                alert_data = []
                for alert in alerts:
                    sla_status = get_sla_status(alert)
                    priority_score = calculate_priority_score(alert)
                    time_to_sla = get_time_to_sla(alert)
                    
                    # Format SLA indicator
                    if sla_status == 'PAST_SLA':
                        sla_indicator = f"🔴 Past SLA ({abs(int(time_to_sla))} min)"
                    elif sla_status == 'APPROACHING_SLA':
                        sla_indicator = f"🟡 {int(time_to_sla)} min to SLA"
                    else:
                        sla_indicator = f"🟢 OK ({int(time_to_sla)} min)"
                    
                    alert_data.append({
                        'Alert ID': alert.alert_id,
                        'Severity': alert.severity,
                        'Risk Score': f"{alert.risk_score:.1f}",
                        'Priority': f"{priority_score:.1f}",
                        'SLA Status': sla_indicator,
                        'Status': alert.status,
                        'Age': f"{(datetime.utcnow() - alert.created_at).total_seconds() / 60:.0f} min",
                        'Transaction ID': alert.transaction_id[:15] + '...' if len(alert.transaction_id) > 15 else alert.transaction_id,
                        'Created At': alert.created_at.strftime('%Y-%m-%d %H:%M'),
                        'Analyst': alert.analyst_id or 'Unassigned'
                    })
                
                df_alerts = pd.DataFrame(alert_data)
                
                # Style the dataframe
                def style_severity(val):
                    badge_html = get_severity_badge_html(val)
                    return badge_html
                
                def style_status(val):
                    badge_html = get_status_badge_html(val)
                    return badge_html
                
                # Display with styling
                st.dataframe(df_alerts, use_container_width=True, hide_index=True, height=400)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Alert detail view
                st.markdown("### 🔍 Alert Investigation")
                
                alert_ids = [a.alert_id for a in alerts]
                selected_alert_id = st.selectbox(
                    "**Select Alert to View Details:**",
                    alert_ids,
                    key="alert_selector",
                    label_visibility="visible"
                )
                
                if selected_alert_id:
                    alert = session.query(Alert).filter(Alert.alert_id == selected_alert_id).first()
                    
                    if alert:
                        # Log view action
                        log_audit_action(selected_alert_id, analyst_id, "VIEWED", "Alert details viewed")
                        
                        # Create professional detail cards
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown('<div class="section-container">', unsafe_allow_html=True)
                            st.markdown("#### 📋 Alert Information")
                            
                            priority_score = calculate_priority_score(alert)
                            sla_status = get_sla_status(alert)
                            time_to_sla = get_time_to_sla(alert)
                            
                            st.markdown(f"**Alert ID:** `{alert.alert_id}`")
                            st.markdown(f"**Severity:** {get_severity_badge_html(alert.severity)}", unsafe_allow_html=True)
                            st.markdown(f"**Risk Score:** **{alert.risk_score:.1f}** / 100")
                            st.markdown(f"**Priority Score:** **{priority_score:.1f}** / 100")
                            st.markdown(f"**SLA Status:** {get_sla_badge_html(sla_status, time_to_sla)}", unsafe_allow_html=True)
                            
                            if time_to_sla < 0:
                                st.markdown(f"**⏱️ Time Past SLA:** **{abs(int(time_to_sla))} minutes**")
                            else:
                                st.markdown(f"**⏱️ Time to SLA:** **{int(time_to_sla)} minutes**")
                            
                            st.markdown(f"**Status:** {get_status_badge_html(alert.status)}", unsafe_allow_html=True)
                            st.markdown(f"**Rule Triggered:** `{alert.rule_triggered}`")
                            st.markdown(f"**Created:** {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                            st.markdown(f"**Age:** {(datetime.utcnow() - alert.created_at).total_seconds() / 60:.0f} minutes")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Get transaction details
                        transaction = session.query(Transaction).filter(
                            Transaction.transaction_id == alert.transaction_id
                        ).first()
                        
                        with col2:
                            st.markdown('<div class="section-container">', unsafe_allow_html=True)
                            st.markdown("#### 💳 Transaction Details")
                            
                            if transaction:
                                st.markdown(f"**Transaction ID:** `{transaction.transaction_id}`")
                                st.markdown(f"**Customer ID:** `{transaction.customer_id}`")
                                st.markdown(f"**Merchant:** **{transaction.merchant}**")
                                st.markdown(f"**Amount:** **${transaction.amount:,.2f}**")
                                st.markdown(f"**Date:** {transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
                                st.markdown(f"**Location:** {transaction.city}, {transaction.country}")
                                st.markdown(f"**Device ID:** `{transaction.device_id}`")
                                st.markdown(f"**IP Address:** `{transaction.ip_address}`")
                                st.markdown(f"**MCC Code:** `{transaction.mcc_code}`")
                                
                                if st.button("👤 View Customer Profile", key="view_customer", use_container_width=True):
                                    st.session_state.customer_id_to_view = transaction.customer_id
                                    st.session_state.view_mode = "Customer Profile"
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Alert notes
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 📝 Alert Notes")
                        st.markdown('<div class="info-box">', unsafe_allow_html=True)
                        st.markdown(alert.notes or "*No notes available for this alert.*")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Action buttons
                        st.markdown("#### ⚡ Quick Actions")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if st.button("🚨 Escalate", key="escalate", use_container_width=True):
                                alert.status = 'ESCALATED'
                                alert.analyst_id = analyst_id
                                session.commit()
                                log_audit_action(selected_alert_id, analyst_id, "ESCALATED", "Alert escalated")
                                st.success("✅ Alert escalated successfully!")
                                st.rerun()
                        
                        with col2:
                            if st.button("✅ Resolve", key="resolve", use_container_width=True):
                                alert.status = 'RESOLVED'
                                alert.resolved_at = datetime.utcnow()
                                alert.analyst_id = analyst_id
                                session.commit()
                                log_audit_action(selected_alert_id, analyst_id, "RESOLVED", "Alert resolved")
                                st.success("✅ Alert resolved successfully!")
                                st.rerun()
                        
                        with col3:
                            if st.button("❌ Dismiss", key="dismiss", use_container_width=True):
                                alert.status = 'DISMISSED'
                                alert.analyst_id = analyst_id
                                session.commit()
                                log_audit_action(selected_alert_id, analyst_id, "DISMISSED", "Alert dismissed as false positive")
                                st.success("✅ Alert dismissed successfully!")
                                st.rerun()
                        
                        with col4:
                            if st.button("📝 Set Reviewing", key="reviewing", use_container_width=True):
                                alert.status = 'REVIEWING'
                                alert.analyst_id = analyst_id
                                session.commit()
                                log_audit_action(selected_alert_id, analyst_id, "REVIEWING", "Alert set to reviewing status")
                                st.success("✅ Alert status updated!")
                                st.rerun()
                        
                        # Add notes
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 💬 Add Notes")
                        new_note = st.text_area("Enter your notes here:", key="note_input", height=100,
                                              placeholder="Type your investigation notes, findings, or actions taken...")
                        if st.button("💾 Save Note", key="save_note", use_container_width=True):
                            if new_note.strip():
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
                        
                        # Show audit log
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("#### 📜 Audit Trail")
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
            
            # Charts section
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📊 Analytics Dashboard")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if alerts:
                    severity_counts = pd.Series([a.severity for a in alerts]).value_counts()
                    st.bar_chart(severity_counts)
                    st.caption("**Alert Distribution by Severity**")
            
            with col2:
                if alerts:
                    status_counts = pd.Series([a.status for a in alerts]).value_counts()
                    st.bar_chart(status_counts)
                    st.caption("**Alert Distribution by Status**")
        
        elif view_mode == "Customer Profile":
            st.markdown("### 👤 Customer Risk Profile & Investigation")
            
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


if __name__ == '__main__':
    main()
