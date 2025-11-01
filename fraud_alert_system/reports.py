"""Daily report generator for alerts and audit logs."""
import pandas as pd
from fraud_alert_system.database import get_session, Alert, Transaction, AuditLog
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def export_alerts_to_excel(filepath='data/daily_report.xlsx', days=1):
    """Export alerts and audit logs to Excel file."""
    session = get_session()
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Get alerts
        alerts = session.query(Alert).filter(
            Alert.created_at >= start_date
        ).order_by(Alert.created_at.desc()).all()
        
        # Get audit logs
        audit_logs = session.query(AuditLog).filter(
            AuditLog.timestamp >= start_date
        ).order_by(AuditLog.timestamp.desc()).all()
        
        # Prepare alert data
        alert_data = []
        for alert in alerts:
            transaction = session.query(Transaction).filter(
                Transaction.transaction_id == alert.transaction_id
            ).first()
            
            alert_data.append({
                'Alert ID': alert.alert_id,
                'Transaction ID': alert.transaction_id,
                'Customer ID': transaction.customer_id if transaction else 'N/A',
                'Merchant': transaction.merchant if transaction else 'N/A',
                'Amount': f"${transaction.amount:,.2f}" if transaction else 'N/A',
                'Severity': alert.severity,
                'Risk Score': alert.risk_score,
                'Status': alert.status,
                'Rule Triggered': alert.rule_triggered,
                'Analyst': alert.analyst_id or 'Unassigned',
                'Created At': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Resolved At': alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if alert.resolved_at else 'N/A',
                'Notes': alert.notes or ''
            })
        
        # Prepare audit log data
        audit_data = []
        for log in audit_logs:
            audit_data.append({
                'Log ID': log.log_id,
                'Alert ID': log.alert_id,
                'Analyst ID': log.analyst_id,
                'Action': log.action,
                'Details': log.details or '',
                'Timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create Excel file with multiple sheets
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Alerts sheet
            df_alerts = pd.DataFrame(alert_data)
            df_alerts.to_excel(writer, sheet_name='Alerts', index=False)
            
            # Audit Log sheet
            df_audit = pd.DataFrame(audit_data)
            df_audit.to_excel(writer, sheet_name='Audit Log', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Alerts',
                    'Open Alerts',
                    'Resolved Alerts',
                    'Escalated Alerts',
                    'Critical Alerts',
                    'High Alerts',
                    'Medium Alerts',
                    'Low Alerts',
                    'Total Audit Actions'
                ],
                'Count': [
                    len(alerts),
                    len([a for a in alerts if a.status == 'OPEN']),
                    len([a for a in alerts if a.status == 'RESOLVED']),
                    len([a for a in alerts if a.status == 'ESCALATED']),
                    len([a for a in alerts if a.severity == 'CRITICAL']),
                    len([a for a in alerts if a.severity == 'HIGH']),
                    len([a for a in alerts if a.severity == 'MEDIUM']),
                    len([a for a in alerts if a.severity == 'LOW']),
                    len(audit_logs)
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"✓ Exported report to {filepath}")
        print(f"  - {len(alerts)} alerts")
        print(f"  - {len(audit_logs)} audit log entries")
        
        return filepath
    
    except Exception as e:
        print(f"✗ Error generating report: {e}")
        raise
    finally:
        session.close()


def export_alerts_to_pdf(filepath='data/daily_report.pdf', days=1):
    """Export alerts summary to PDF file."""
    session = get_session()
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Get alerts
        alerts = session.query(Alert).filter(
            Alert.created_at >= start_date
        ).order_by(Alert.created_at.desc()).all()
        
        # Get summary statistics
        total_alerts = len(alerts)
        open_alerts = len([a for a in alerts if a.status == 'OPEN'])
        resolved_alerts = len([a for a in alerts if a.status == 'RESOLVED'])
        critical_alerts = len([a for a in alerts if a.severity == 'CRITICAL'])
        
        # Create PDF
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Daily Fraud Alert Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Date
        date_str = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        date_para = Paragraph(date_str, styles['Normal'])
        story.append(date_para)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        summary_title = Paragraph("Summary Statistics", styles['Heading2'])
        story.append(summary_title)
        
        summary_data = [
            ['Metric', 'Count'],
            ['Total Alerts', str(total_alerts)],
            ['Open Alerts', str(open_alerts)],
            ['Resolved Alerts', str(resolved_alerts)],
            ['Critical Alerts', str(critical_alerts)]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top alerts table
        alerts_title = Paragraph("Recent Alerts (Top 20)", styles['Heading2'])
        story.append(alerts_title)
        
        alerts_data = [['Alert ID', 'Severity', 'Status', 'Risk Score', 'Created']]
        for alert in alerts[:20]:
            alerts_data.append([
                alert.alert_id[:10] + '...',
                alert.severity,
                alert.status,
                f"{alert.risk_score:.1f}",
                alert.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        alerts_table = Table(alerts_data)
        alerts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        story.append(alerts_table)
        
        # Build PDF
        doc.build(story)
        print(f"✓ Exported PDF report to {filepath}")
        return filepath
    
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    import sys
    
    export_format = sys.argv[1] if len(sys.argv) > 1 else 'excel'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    if export_format.lower() == 'pdf':
        export_alerts_to_pdf(days=days)
    else:
        export_alerts_to_excel(days=days)

