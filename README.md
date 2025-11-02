[![Docs](https://img.shields.io/badge/docs-Quickstart-blue)](QUICKSTART.md)
[![Guide](https://img.shields.io/badge/docs-User_Guide-green)](USER_GUIDE.md)

# FraudOps Alert Management System

A portfolio-grade simulator that mirrors enterprise fraud-alert triage workflows — built to demonstrate Fraud Ops logic, automation, and audit tracking. This system processes transactions, applies rule-based fraud detection, and provides an interactive dashboard for analysts to triage, investigate, and resolve fraud alerts.

## 🎯 Overview

This platform demonstrates end-to-end fraud operations capabilities including:

- **Transaction Processing**: CSV ingestion with SQLite database storage
- **Rule-Based Detection**: 6 fraud detection rules with configurable thresholds
- **Alert Management**: Prioritized alert queue with SLA tracking
- **Investigation Tools**: Customer risk profiles and transaction history
- **Bulk Operations**: Efficient batch processing for high-volume workflows
- **Audit Trail**: Complete compliance logging of all analyst actions
- **Reporting**: Excel and PDF report generation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fraud_alert_management_Simulator
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

**Troubleshooting:** If you encounter `pyarrow` build errors (Python 3.13+ or macOS), use:
```bash
pip install --upgrade pip setuptools wheel
pip install --only-binary :all: -r requirements.txt
```

4. **Initialize database** (optional for local dev, auto-initializes on Streamlit Cloud)
```bash
python setup_database.py
```

5. **Launch dashboard**
```bash
streamlit run app.py
```

**Note**: On Streamlit Cloud, the database and sample data automatically initialize on first deployment. Manual setup is only required for local development.

Access the dashboard at `http://localhost:8501`

## 📋 Key Features

### Fraud Detection Rules
- **High Amount**: Flags transactions > $5,000
- **Velocity**: Detects >5 transactions per hour
- **Geo-Jump**: Identifies impossible travel patterns
- **Device Sharing**: Flags devices used by multiple customers
- **Unusual Time**: Detects transactions during 2-5 AM
- **Suspicious Merchant**: Flags high-risk MCC codes

### Alert Management
- **Priority Scoring**: Combines risk score and SLA urgency
- **SLA Tracking**: Automatic deadline monitoring (15 min to 24 hours by severity)
- **Smart Sorting**: Priority, risk score, or date-based ordering
- **Bulk Operations**: Process multiple alerts simultaneously
- **Customer Profiles**: Complete investigation context with risk aggregation

### Dashboard Features
- Professional UI with enhanced color-coded severity/status badges
- Real-time alert metrics with tooltips and visual feedback
- Interactive filtering (Status, Severity, Date Range, Merchant, Analyst)
- Comprehensive analytics dashboard with charts
- Mini audit log feed showing recent system activity
- Transaction detail views with customer linking
- Complete audit trail for compliance
- Excel/PDF report generation
- Auto-initialization for Streamlit Cloud deployments

## 📁 Project Structure

```
fraud_alert_management_Simulator/
├── fraud_alert_system/
│   ├── database.py           # Database schema & connection
│   ├── data_generator.py     # Synthetic transaction generator
│   ├── ingestion.py          # CSV to database loader
│   ├── fraud_engine.py       # Rule-based fraud detection
│   ├── priority_manager.py   # Alert prioritization & SLA tracking
│   ├── customer_profiles.py # Customer risk aggregation
│   ├── dashboard.py          # Streamlit web interface
│   └── reports.py            # Excel/PDF report generator
├── tests/
│   └── test_fraud_engine.py  # Unit tests
├── app.py                    # Dashboard entry point
├── setup_database.py         # Database initialization script
├── requirements.txt          # Python dependencies
├── QUICKSTART.md            # Quick reference guide
└── USER_GUIDE.md            # Comprehensive documentation
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

## 📚 Documentation

- **QUICKSTART.md**: Quick reference for common tasks
- **USER_GUIDE.md**: Comprehensive guide covering all features, terminology, workflows, and usage

## 🔧 Usage Examples

### Generate More Transactions
```python
from fraud_alert_system.data_generator import generate_transactions, save_transactions_to_csv

df = generate_transactions(num_transactions=1000, days_back=60)
save_transactions_to_csv(df, 'data/new_transactions.csv')
```

### Generate Reports
```bash
# Excel report (last 1 day)
python -m fraud_alert_system.reports excel 1

# PDF report (last 7 days)
python -m fraud_alert_system.reports pdf 7
```

## 🎯 Use Cases

- **Fraud Operations Training**: Learn fraud detection workflows
- **Portfolio Project**: Demonstrate data engineering and fraud ops skills
- **System Design Practice**: Study end-to-end system architecture
- **Interview Preparation**: Showcase fraud operations understanding

## 🛠️ Built With

- **Python 3.8+**: Core language
- **Streamlit**: Web dashboard framework
- **SQLAlchemy**: Database ORM
- **Pandas**: Data processing
- **SQLite**: Embedded database

## 📝 License

This project is for educational and demonstration purposes.

---

**For detailed documentation**, see [USER_GUIDE.md](USER_GUIDE.md)
