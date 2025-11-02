# Quick Start Guide

## 1. Install Dependencies

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

**Troubleshooting Installation:**
- For Python 3.13+ or if you encounter build errors (especially with `pyarrow`), use pre-built wheels:
  ```bash
  pip install --upgrade pip setuptools wheel
  pip install --only-binary :all: -r requirements.txt
  ```

## 2. Initialize Database and Load Data

Run the setup script to initialize everything:
```bash
python setup_database.py
```

This will:
- Create the SQLite database
- Generate 500 synthetic transactions (with variety of severity levels)
- Run fraud detection rules
- Generate initial alerts

**Note:** On Streamlit Cloud, the database auto-initializes on first run. Manual setup is only needed for local development.

## 3. Launch the Analyst Console

Start the Streamlit dashboard:
```bash
streamlit run app.py
```

Once launched, open `http://localhost:8501` in your browser and navigate to the alerts queue tab to begin reviewing alerts.

## 4. Use the Dashboard

1. Enter your Analyst ID (e.g., "ANALYST001")
2. Browse alerts using the filters
3. Click on an alert to view details
4. Take actions: Escalate, Resolve, Dismiss, or Add Notes
5. View the audit trail for each alert

## 5. Generate Reports

After running reports, open the file in `outputs/` (e.g., `daily_report_2025-11-01.xlsx`) to inspect summary metrics and alert logs.

Generate reports in different formats:
```bash
# Excel report (last 1 day)
python -m fraud_alert_system.reports excel 1

# PDF report (last 7 days)
python -m fraud_alert_system.reports pdf 7
```

## 6. Run Tests

```bash
pytest tests/ -v
```

## Next Steps

- **Learn More**: See [USER_GUIDE.md](USER_GUIDE.md) for comprehensive documentation
- **Generate More Transactions**: Modify `data_generator.py` and re-run `setup_database.py`
- **Customize Fraud Rules**: Edit `fraud_engine.py` to adjust thresholds or add rules
- **Enhance Dashboard**: Modify `dashboard.py` to add features
- **Add ML Scoring**: Integrate a model into `fraud_engine.py`

For detailed information on all features, workflows, and terminology, see [USER_GUIDE.md](USER_GUIDE.md).

