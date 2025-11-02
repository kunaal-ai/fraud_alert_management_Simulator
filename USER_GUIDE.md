# FraudOps Alert Management System - User Guide

Comprehensive documentation covering all aspects of the FraudOps Alert Management System.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Terminology](#terminology)
3. [System Architecture](#system-architecture)
4. [Components](#components)
5. [Workflows](#workflows)
6. [Fraud Detection Rules](#fraud-detection-rules)
7. [Dashboard Usage](#dashboard-usage)
8. [Database Schema](#database-schema)
9. [Priority & SLA System](#priority--sla-system)
10. [Customer Risk Profiles](#customer-risk-profiles)
11. [Bulk Operations](#bulk-operations)
12. [Reporting](#reporting)
13. [API & Scripts](#api--scripts)

---

## System Overview

This simulator replicates a bank's fraud-alert workflow—from transaction ingestion and scoring to analyst triage and audit-logging. It processes financial transactions, identifies suspicious activity through rule-based detection, and provides tools for fraud analysts to investigate and resolve alerts.

### What This System Does

1. **Ingests** transaction data from CSV files
2. **Analyzes** each transaction using multiple fraud detection rules
3. **Generates** alerts for suspicious transactions with risk scoring
4. **Prioritizes** alerts based on risk and SLA deadlines
5. **Presents** alerts to analysts through an interactive dashboard where they can review alerts and choose actions—Escalate, Dismiss or Monitor—with full audit trail for compliance tracking
6. **Tracks** all analyst actions in a complete audit trail
7. **Generates** reports for management and compliance

### Key Capabilities

- **Transaction Processing**: Handles CSV data ingestion and database storage
- **Multi-Rule Detection**: 6 different fraud detection rules with weighted scoring
- **Intelligent Prioritization**: Combines risk scores with SLA urgency
- **Investigation Tools**: Customer risk profiles and transaction history
- **Operational Efficiency**: Bulk operations for high-volume processing
- **Compliance**: Complete audit logging of all activities

---

## Terminology

### Core Concepts

**Transaction**: A single financial transaction record containing customer, merchant, amount, location, device, and timestamp information.

**Alert**: A flag generated when a transaction triggers one or more fraud detection rules. Contains risk score, severity, and status.

**Risk Score**: A numeric value (0-100) representing the overall fraud risk of a transaction, calculated from triggered rules.

**Severity**: A categorical classification of alert importance:
- **CRITICAL**: Risk score ≥ 80 (highest priority)
- **HIGH**: Risk score 60-79
- **MEDIUM**: Risk score 40-59
- **LOW**: Risk score < 40 (lowest priority)

**SLA (Service Level Agreement)**: Time-based deadlines for alert review:
- CRITICAL: 15 minutes
- HIGH: 1 hour
- MEDIUM: 4 hours
- LOW: 24 hours

**Priority Score**: A combined metric (0-100) that considers both risk score and SLA urgency for queue ordering.

**False Positive**: An alert that, upon investigation, is determined to be legitimate activity.

**Triage**: The process of reviewing, categorizing, and routing alerts to appropriate analysts.

**Audit Trail**: A complete log of all actions taken on alerts, including who performed the action, when, and why.

### Alert Statuses

- **OPEN**: Newly created alert, not yet reviewed
- **REVIEWING**: Alert is currently being investigated by an analyst
- **ESCALATED**: Alert requires higher-level review or approval
- **DISMISSED**: Alert determined to be false positive
- **RESOLVED**: Alert investigated and fraud confirmed/blocked

---

## System Architecture

### High-Level Flow

```
CSV Transactions
    ↓
[Ingestion Module] → SQLite Database
    ↓
[Fraud Detection Engine] → Generate Alerts
    ↓
[Priority Manager] → Calculate Priority & SLA
    ↓
[Dashboard] → Analyst Interface
    ↓
[Analyst Actions] → Update Alert Status
    ↓
[Audit Log] → Track All Actions
    ↓
[Reports] → Generate Excel/PDF
```

### Component Interactions

1. **Data Generator** → Creates synthetic transaction data
2. **Ingestion** → Loads transactions into database
3. **Fraud Engine** → Analyzes transactions and generates alerts
4. **Priority Manager** → Calculates priority scores and SLA status
5. **Dashboard** → Presents alerts to analysts
6. **Customer Profiles** → Aggregates customer risk data
7. **Reports** → Generates formatted reports

### Database Structure

The system uses SQLite with three main tables:
- **transactions**: Stores all transaction records
- **alerts**: Stores fraud alerts linked to transactions
- **audit_log**: Stores all analyst actions for compliance

---

## Components

### 1. Database Module (`database.py`)

**Purpose**: Manages database schema, connections, and table definitions.

**Key Classes**:
- `Transaction`: Transaction record schema
- `Alert`: Alert record schema with severity and status
- `AuditLog`: Audit trail record schema

**Functions**:
- `create_database()`: Initialize database and tables
- `get_session()`: Create database session for queries

**Usage**:
```python
from fraud_alert_system.database import get_session, Transaction, Alert

session = get_session()
transactions = session.query(Transaction).all()
```

### 2. Data Generator (`data_generator.py`)

**Purpose**: Creates synthetic transaction data for testing and demonstration.

**Key Functions**:
- `generate_transactions(num_transactions, days_back)`: Create synthetic transactions
- `save_transactions_to_csv(df, filepath)`: Export to CSV

**Features**:
- Realistic transaction patterns
- Configurable volume and time range
- Includes fraud patterns for testing

**Usage**:
```python
from fraud_alert_system.data_generator import generate_transactions, save_transactions_to_csv

df = generate_transactions(num_transactions=1000, days_back=30)
save_transactions_to_csv(df, 'data/transactions.csv')
```

### 3. Ingestion Module (`ingestion.py`)

**Purpose**: Loads transaction data from CSV files into the database.

**Key Functions**:
- `load_transactions_from_csv(filepath)`: Parse CSV and insert into database

**Features**:
- Validates transaction data
- Handles duplicates
- Provides loading progress feedback

**Usage**:
```bash
python -m fraud_alert_system.ingestion data/transactions.csv
```

### 4. Fraud Detection Engine (`fraud_engine.py`)

**Purpose**: Analyzes transactions using rule-based detection and generates alerts.

**Key Class**: `FraudDetectionEngine`

**Detection Rules**:
1. High Amount Rule
2. Velocity Rule
3. Geo-Jump Rule
4. Device Sharing Rule
5. Unusual Time Rule
6. Suspicious Merchant Rule

**Key Methods**:
- `analyze_transaction(transaction)`: Run all rules on a transaction
- `calculate_risk_score(rules_triggered)`: Calculate 0-100 risk score
- `get_severity(risk_score)`: Map risk to severity level
- `generate_alert(transaction, rules_triggered)`: Create alert record
- `process_transactions(limit)`: Batch process transactions

**Risk Score Calculation**:
- Each rule has a weight:
  - HIGH_AMOUNT: 30 points
  - VELOCITY: 25 points
  - GEO_JUMP: 20 points
  - DEVICE_SHARING: 15 points
  - SUSPICIOUS_MERCHANT: 15 points
  - UNUSUAL_TIME: 10 points
- Risk score = sum of triggered rule weights (capped at 100)

**Usage**:
```python
from fraud_alert_system.fraud_engine import FraudDetectionEngine

engine = FraudDetectionEngine()
alerts_generated = engine.process_transactions()
engine.close()
```

### 5. Priority Manager (`priority_manager.py`)

**Purpose**: Calculates alert priority and tracks SLA compliance.

**Key Functions**:
- `calculate_priority_score(alert)`: Calculate combined priority (0-100)
- `get_sla_status(alert)`: Determine if alert is past/approaching/OK
- `get_time_to_sla(alert)`: Get minutes until SLA breach
- `sort_alerts_by_priority(alerts)`: Sort alerts by priority

**Priority Score Formula**:
```
Priority = (Risk Score × 0.6) + (Age Penalty × 0.4)

Age Penalty:
- Before SLA: (age / SLA_threshold) × 40
- After SLA: 40 + min(60, (over_SLA / SLA_threshold) × 60)
```

**SLA Thresholds**:
- CRITICAL: 15 minutes
- HIGH: 1 hour (60 minutes)
- MEDIUM: 4 hours (240 minutes)
- LOW: 24 hours (1440 minutes)

### 6. Customer Profiles (`customer_profiles.py`)

**Purpose**: Aggregates customer-level risk information for investigation context.

**Key Function**: `get_customer_risk_profile(customer_id, session)`

**Returns**:
- Total alerts and transactions
- Average and maximum risk scores
- Severity and status breakdowns
- Transaction statistics (totals, averages, recent activity)
- Pattern indicators (unique locations, devices)
- Recent alerts and transactions

**Usage**:
```python
from fraud_alert_system.customer_profiles import get_customer_risk_profile

profile = get_customer_risk_profile('CUST12345678', session)
print(profile['avg_risk_score'])
```

### 7. Dashboard (`dashboard.py`)

**Purpose**: Interactive web interface for fraud analysts.

**Features**:
- Alert queue with filtering and sorting
- Priority and SLA indicators
- Alert detail investigation view
- Customer risk profiles
- Bulk operations
- Analytics charts
- Audit trail viewing

**Views**:
- **Alert Queue**: Main alert triage interface
- **Customer Profile**: Customer investigation view

### 8. Reports (`reports.py`)

**Purpose**: Generate formatted reports in Excel and PDF formats.

**Key Functions**:
- `export_alerts_to_excel(filepath, days)`: Generate Excel report
- `export_alerts_to_pdf(filepath, days)`: Generate PDF report

**Report Contents**:
- Alert summaries with details
- Audit log entries
- Statistics and metrics
- Time-based filtering

**Usage**:
```bash
python -m fraud_alert_system.reports excel 1  # Last 1 day
python -m fraud_alert_system.reports pdf 7    # Last 7 days
```

---

## Workflows

### Standard Alert Triage Workflow

1. **Analyst logs in** to dashboard with Analyst ID
2. **Views alert queue** sorted by priority (default)
3. **Filters alerts** by status, severity, or date range
4. **Selects alert** to investigate
5. **Reviews alert details**:
   - Risk score and severity
   - Priority and SLA status
   - Transaction information
   - Triggered rules
6. **Views customer profile** (if needed) for context
7. **Takes action**:
   - Escalate (requires higher review)
   - Resolve (fraud confirmed)
   - Dismiss (false positive)
   - Set to Reviewing (in progress)
8. **Adds notes** documenting investigation
9. **All actions logged** in audit trail

### Bulk Processing Workflow

1. **Analyst selects multiple alerts** using multiselect
2. **Reviews selected alerts** (shown in selection count)
3. **Chooses bulk action**:
   - Bulk Resolve
   - Bulk Dismiss
4. **Confirms action** - system processes all selected alerts
5. **Verifies results** - success message shows count
6. **All actions logged** individually in audit trail

### Customer Investigation Workflow

1. **Analyst identifies customer** from alert transaction
2. **Clicks "View Customer Profile"** or navigates to Customer Profile view
3. **Enters Customer ID** or uses link from alert
4. **Reviews customer overview**:
   - Risk metrics (average, max risk scores)
   - Alert counts by severity and status
   - Transaction statistics
   - Pattern indicators
5. **Examines recent alerts** for patterns
6. **Reviews transaction history** for context
7. **Makes informed decision** based on full context

### Reporting Workflow

1. **Analyst or manager** needs daily/weekly report
2. **Runs report command**:
   ```bash
   python -m fraud_alert_system.reports excel 1
   ```
3. **System generates report** with:
   - All alerts in time period
   - Audit log entries
   - Summary statistics
4. **Report saved** to `data/` directory
5. **Opens report** in Excel/PDF viewer
6. **Shares with stakeholders** for review

---

## Fraud Detection Rules

### 1. High Amount Rule

**Purpose**: Flags unusually large transactions that exceed normal spending patterns.

**Threshold**: $5,000

**Logic**: 
```python
if transaction.amount > 5000:
    trigger_rule()
```

**Weight**: 30 points

**Use Case**: Large transactions may indicate account takeover, unauthorized purchases, or money laundering.

### 2. Velocity Rule

**Purpose**: Detects rapid-fire transactions that may indicate card testing or fraudulent spending spree.

**Threshold**: More than 5 transactions within 1 hour

**Logic**:
```python
count = transactions_in_last_hour(customer_id)
if count >= 5:
    trigger_rule()
```

**Weight**: 25 points

**Use Case**: Fraudsters often test cards or make quick purchases before card is blocked.

### 3. Geo-Jump Rule

**Purpose**: Identifies physically impossible travel patterns.

**Threshold**: Different city/country within 2 hours

**Logic**:
```python
recent_locations = get_locations_in_last_2_hours(customer_id)
if current_location not in recent_locations:
    trigger_rule()
```

**Weight**: 20 points

**Use Case**: Legitimate customers cannot be in two distant locations within hours.

### 4. Device Sharing Rule

**Purpose**: Flags devices used by multiple customers, indicating potential card sharing or compromised devices.

**Threshold**: Device used by 3+ different customers in 7 days

**Logic**:
```python
unique_customers = count_unique_customers(device_id, last_7_days)
if unique_customers >= 3:
    trigger_rule()
```

**Weight**: 15 points

**Use Case**: Legitimate devices are typically associated with one customer.

### 5. Unusual Time Rule

**Purpose**: Flags transactions during typically inactive hours.

**Threshold**: Transactions between 2 AM and 5 AM

**Logic**:
```python
if transaction.hour >= 2 and transaction.hour <= 5:
    trigger_rule()
```

**Weight**: 10 points

**Use Case**: Late-night transactions may indicate automated fraud or compromised accounts.

### 6. Suspicious Merchant Rule

**Purpose**: Flags transactions at known high-risk merchant categories.

**Threshold**: Specific MCC codes (gaming, adult entertainment, etc.)

**MCC Codes**:
- 7995: Digital Gaming
- 7273: Adult Entertainment
- 5967: Direct Marketing
- 5912: Drug Stores

**Logic**:
```python
high_risk_mccs = ["7995", "7273", "5967", "5912"]
if transaction.mcc_code in high_risk_mccs:
    trigger_rule()
```

**Weight**: 15 points

**Use Case**: Some merchant categories have higher fraud rates.

---

## Dashboard Usage

### Getting Started

1. **Launch Dashboard**:
   ```bash
   streamlit run app.py
   ```

2. **Enter Analyst ID**: Enter your analyst identifier (e.g., "ANALYST001")

3. **Select View Mode**: Choose between "Alert Queue" or "Customer Profile"

### Alert Queue View

#### Summary Metrics

The top of the dashboard shows 5 key metrics:
- **Total Alerts**: Count of all alerts matching filters
- **Open Alerts**: Alerts not yet resolved/dismissed
- **Critical**: CRITICAL severity alerts (immediate attention)
- **Escalated**: Alerts requiring higher-level review
- **Past SLA**: Alerts that have exceeded their SLA deadline

#### Filters

Use sidebar filters to narrow alerts:
- **Alert Status**: Filter by OPEN, REVIEWING, ESCALATED, DISMISSED, RESOLVED
- **Severity Level**: Filter by CRITICAL, HIGH, MEDIUM, LOW
- **Date Range**: Select time period for alerts
- **Sort By**: Choose sorting method
  - Priority (Highest First) - Recommended default
  - Created Date (Newest/Oldest)
  - Risk Score (Highest)

#### Bulk Operations

1. **Select Alerts**: Use multiselect dropdown to choose multiple alerts
2. **Review Selection**: Check the count of selected alerts
3. **Choose Action**:
   - **Resolve Selected**: Mark all selected as resolved
   - **Dismiss Selected**: Mark all selected as false positives
4. **Confirm**: System processes all alerts and shows success message

#### Alert Table

The table displays:
- **Alert ID**: Unique identifier
- **Severity**: Color-coded badge (CRITICAL/HIGH/MEDIUM/LOW)
- **Risk Score**: 0-100 numeric score
- **Priority**: Combined priority score
- **SLA Status**: Visual indicator with time remaining/overdue
- **Status**: Current alert status
- **Age**: Minutes since alert creation
- **Transaction ID**: Linked transaction
- **Created At**: Timestamp
- **Analyst**: Assigned analyst

#### Alert Details

When you select an alert:

**Alert Information Panel**:
- Alert ID, Severity, Risk Score
- Priority Score (combined metric)
- SLA Status with time remaining/past
- Status and triggered rules
- Creation timestamp and age

**Transaction Details Panel**:
- Transaction ID, Customer ID, Merchant
- Amount, Date, Location
- Device ID, IP Address, MCC Code
- **"View Customer Profile"** button for context

**Actions**:
- **Escalate**: Requires higher-level review
- **Resolve**: Fraud confirmed, case closed
- **Dismiss**: False positive, no fraud
- **Set Reviewing**: Mark as in-progress

**Notes Section**:
- View existing notes
- Add new investigation notes
- Notes timestamped automatically

**Audit Trail**:
- Complete log of all actions
- Shows who, what, when, and why

### Customer Profile View

#### Accessing Customer Profile

**From Alert Detail**:
- Click "View Customer Profile" button in transaction details

**From Sidebar**:
- Select "Customer Profile" view mode
- Enter Customer ID manually

#### Profile Sections

**Risk Overview Metrics**:
- Total Alerts: All alerts for this customer
- Avg Risk Score: Average risk across all alerts
- Max Risk Score: Highest risk alert
- Total Transactions: Lifetime transaction count

**Alert Breakdown Charts**:
- Alerts by Severity: Distribution of CRITICAL/HIGH/MEDIUM/LOW
- Alerts by Status: Distribution of OPEN/RESOLVED/DISMISSED/etc.

**Transaction Statistics**:
- Total Amount: Lifetime spending
- Avg Transaction: Average transaction size
- Max Transaction: Largest single transaction
- Recent Activity: Transactions in last 7 days

**Pattern Indicators**:
- Unique Locations: Geographic spread
- Unique Devices: Device diversity (higher may indicate sharing)

**Recent Alerts Table**:
- Last 10 alerts with severity, risk score, status
- Clickable to navigate back to alert detail

**Recent Transactions Table**:
- Last 20 transactions with merchant, amount, location, device
- Helps identify spending patterns

---

## Database Schema

### Transactions Table

Stores all transaction records:

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-increment |
| `transaction_id` | String(50) | Unique transaction identifier (indexed) |
| `customer_id` | String(50) | Customer identifier (indexed) |
| `merchant` | String(100) | Merchant name |
| `amount` | Float | Transaction amount |
| `currency` | String(3) | Currency code (default: USD) |
| `transaction_date` | DateTime | Transaction timestamp (indexed) |
| `card_type` | String(20) | Card type (Visa, Mastercard, etc.) |
| `device_id` | String(50) | Device identifier (indexed) |
| `ip_address` | String(45) | IP address |
| `country` | String(50) | Country |
| `city` | String(100) | City |
| `mcc_code` | String(10) | Merchant Category Code |
| `status` | String(20) | Transaction status (default: completed) |
| `created_at` | DateTime | Record creation timestamp |

### Alerts Table

Stores fraud alerts:

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-increment |
| `alert_id` | String(50) | Unique alert identifier (indexed) |
| `transaction_id` | String(50) | Foreign key to transactions |
| `rule_triggered` | String(100) | Comma-separated list of triggered rules |
| `severity` | String(20) | CRITICAL/HIGH/MEDIUM/LOW (indexed) |
| `risk_score` | Float | 0-100 risk score |
| `status` | String(20) | OPEN/REVIEWING/ESCALATED/DISMISSED/RESOLVED (indexed) |
| `analyst_id` | String(50) | Assigned analyst identifier |
| `notes` | Text | Analyst investigation notes |
| `created_at` | DateTime | Alert creation timestamp (indexed) |
| `resolved_at` | DateTime | Resolution timestamp (if resolved) |

### Audit Log Table

Stores all analyst actions:

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-increment |
| `log_id` | String(50) | Unique log identifier (indexed) |
| `alert_id` | String(50) | Foreign key to alerts |
| `analyst_id` | String(50) | Analyst who performed action |
| `action` | String(50) | Action type (VIEWED/ESCALATED/RESOLVED/DISMISSED/NOTE_ADDED) |
| `details` | Text | Action details/notes |
| `timestamp` | DateTime | Action timestamp (indexed) |

---

## Priority & SLA System

### How Priority Works

The priority score combines two factors:

1. **Risk Score** (60% weight): The inherent fraud risk
2. **Age Penalty** (40% weight): Urgency based on time past creation

**Formula**:
```
Priority = (Risk Score × 0.6) + (Age Penalty × 0.4)
```

### Age Penalty Calculation

**Before SLA**:
- Penalty increases linearly from 0 to 40 points
- Based on percentage of SLA threshold used
- Example: 50% through SLA = 20 points

**After SLA**:
- Penalty jumps to 40+ and increases exponentially
- Can add up to 60 more points (total 100)
- Very old alerts get maximum priority

### SLA Thresholds by Severity

| Severity | SLA Time | Rationale |
|----------|----------|-----------|
| CRITICAL | 15 minutes | Highest risk requires immediate attention |
| HIGH | 1 hour | Significant risk needs prompt review |
| MEDIUM | 4 hours | Moderate risk allows more time |
| LOW | 24 hours | Low risk can be reviewed within day |

### SLA Status Indicators

- **🟢 OK**: Alert within SLA, no urgency
- **🟡 Approaching SLA**: Within 80% of threshold
- **🔴 Past SLA**: Exceeded deadline, urgent

### Why This Matters

- **Compliance**: Many fraud operations have SLA requirements
- **Risk Mitigation**: Critical alerts need fast response
- **Operational Efficiency**: Priority queue ensures important work first
- **Performance Metrics**: Track SLA compliance for management

---

## Customer Risk Profiles

### Purpose

Customer profiles aggregate risk signals across all transactions to provide investigation context. Analysts need to understand:
- Is this a one-time event or pattern?
- What's the customer's normal behavior?
- Are there previous alerts?
- What are spending patterns?

### Profile Data

**Risk Aggregation**:
- Average risk score across all alerts
- Maximum risk score (worst case)
- Total alert count
- Breakdown by severity and status

**Transaction Statistics**:
- Lifetime totals and averages
- Recent activity (last 7 days)
- Maximum transaction size

**Pattern Indicators**:
- **Unique Locations**: Geographic spread
  - High = possible travel, multiple users, or fraud
  - Low = typical single-location customer
- **Unique Devices**: Device diversity
  - High = possible device sharing or account compromise
  - Low = typical single-device customer

### When to Use

- **Before dismissing**: Check if customer has history of alerts
- **Before escalating**: Verify if this is part of a pattern
- **Before resolving**: Ensure complete context for decision
- **Investigation**: Understand customer's normal behavior vs. anomaly

---

## Bulk Operations

### Purpose

Process multiple alerts simultaneously to improve analyst productivity. Fraud operations handle high volumes, and bulk operations save significant time.

### When to Use Bulk Operations

**Bulk Dismiss**:
- Multiple obvious false positives
- Same customer/merchant pattern
- Similar low-risk alerts

**Bulk Resolve**:
- Confirmed fraud pattern
- Similar cases already investigated
- Batch of related alerts

### How It Works

1. **Select Alerts**: Use multiselect dropdown
2. **Review Selection**: System shows count
3. **Choose Action**: Click bulk button
4. **System Processes**: Updates all selected alerts
5. **Audit Logging**: Each alert action logged separately
6. **Confirmation**: Success message with count

### Best Practices

- **Review before bulk actions**: Ensure all selected alerts are appropriate
- **Use for similar cases**: Bulk actions work best for similar alert types
- **Document reasons**: Add notes explaining bulk action rationale
- **Verify results**: Check that all alerts updated correctly

---

## Reporting

### Report Types

#### Excel Report

**Format**: Multi-sheet Excel workbook

**Sheets**:
1. **Alerts**: All alerts with full details
2. **Audit Log**: All audit entries
3. **Summary**: Statistics and metrics

**Usage**:
```bash
python -m fraud_alert_system.reports excel 1  # Last 1 day
```

#### PDF Report

**Format**: Formatted PDF document

**Contents**:
- Summary statistics
- Recent alerts (top 20)
- Formatted tables and charts

**Usage**:
```bash
python -m fraud_alert_system.reports pdf 7  # Last 7 days
```

### Report Contents

**Alert Information**:
- Alert ID, Transaction ID, Customer ID
- Merchant, Amount, Date
- Severity, Risk Score, Status
- Triggered rules
- Analyst, Notes

**Statistics**:
- Total alerts
- Breakdown by severity and status
- Resolution rates
- Time-based metrics

**Audit Trail**:
- All actions taken
- Analyst IDs
- Timestamps
- Action details

### Use Cases

- **Daily Reports**: Management review of daily operations
- **Weekly Summaries**: Trend analysis and metrics
- **Compliance**: Audit trail documentation
- **Performance**: Analyst productivity metrics

---

## API & Scripts

### Command-Line Interface

#### Setup Database
```bash
python setup_database.py
```
Creates database, generates sample data, and runs fraud detection.

#### Run Fraud Detection
```bash
python -m fraud_alert_system.fraud_engine
```
Processes unanalyzed transactions and generates alerts.

#### Generate Reports
```bash
python -m fraud_alert_system.reports excel 1
python -m fraud_alert_system.reports pdf 7
```

#### Load Transactions
```bash
python -m fraud_alert_system.ingestion data/transactions.csv
```

### Python API

#### Generate Transactions
```python
from fraud_alert_system.data_generator import generate_transactions, save_transactions_to_csv

# Generate 1000 transactions over last 60 days
df = generate_transactions(num_transactions=1000, days_back=60)
save_transactions_to_csv(df, 'data/new_transactions.csv')
```

#### Process Transactions
```python
from fraud_alert_system.fraud_engine import FraudDetectionEngine

engine = FraudDetectionEngine()
alerts = engine.process_transactions(limit=100)  # Process first 100
engine.close()
```

#### Query Database
```python
from fraud_alert_system.database import get_session, Alert, Transaction

session = get_session()
alerts = session.query(Alert).filter(Alert.status == 'OPEN').all()
```

#### Customer Profile
```python
from fraud_alert_system.customer_profiles import get_customer_risk_profile

session = get_session()
profile = get_customer_risk_profile('CUST12345678', session)
print(f"Average Risk: {profile['avg_risk_score']}")
```

---

## Troubleshooting

### Common Issues

**Database not found**:
- Run `python setup_database.py` first
- Check that `data/` directory exists

**No alerts showing**:
- Run fraud detection: `python -m fraud_alert_system.fraud_engine`
- Check filters in dashboard
- Verify transactions loaded: `session.query(Transaction).count()`

**Import errors**:
- Ensure virtual environment activated
- Install dependencies: `pip install -r requirements.txt`

**Dashboard not loading**:
- Check Streamlit installed: `pip install streamlit`
- Verify port 8501 available
- Check for errors in terminal

---

## Best Practices

### For Analysts

1. **Prioritize by Priority Score**: Use default sorting for efficiency
2. **Check SLA Status**: Address past-SLA alerts immediately
3. **Use Customer Profiles**: Get full context before decisions
4. **Document Thoroughly**: Add detailed notes for future reference
5. **Use Bulk Operations**: Save time on similar cases
6. **Verify Before Bulk Dismiss**: Ensure false positives are accurate

### For System Administrators

1. **Regular Reports**: Generate daily/weekly reports
2. **Monitor SLA Compliance**: Track past-SLA metrics
3. **Database Maintenance**: Regular backups of SQLite database
4. **Performance Monitoring**: Watch for slow queries with large datasets
5. **Update Rules**: Adjust thresholds based on false positive rates

### For Developers

1. **Add Custom Rules**: Extend `fraud_engine.py` with new rules
2. **Modify Thresholds**: Update rule weights and thresholds
3. **Enhance Dashboard**: Add new views or features
4. **Extend Reports**: Customize report formats
5. **Add Tests**: Expand test coverage

---

## Conclusion

This guide covers all aspects of the FraudOps Alert Management System. For quick reference, see [QUICKSTART.md](QUICKSTART.md). For system overview, see [README.md](README.md).

**Questions or Issues?**
- Review this guide for common solutions
- Check troubleshooting section
- Review code comments for implementation details

