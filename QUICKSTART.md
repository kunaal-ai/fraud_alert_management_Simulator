# Quick Start Guide

## 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Troubleshooting Installation:**
- If you encounter build errors (especially with `pyarrow` on Python 3.13+), use pre-built wheels instead:
  ```bash
  pip install --upgrade pip setuptools wheel
  pip install --only-binary :all: -r requirements.txt
  ```

## 2. Initialize Database and Load Data

```bash
python setup_database.py
```

This will:
- Create the database
- Generate 500 synthetic transactions
- Load them into the database
- Run fraud detection and generate alerts

## 3. Launch Dashboard

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 4. Use the Dashboard

1. Enter your Analyst ID (e.g., "ANALYST001")
2. Browse alerts using the filters
3. Click on an alert to view details
4. Take actions: Escalate, Resolve, Dismiss, or Add Notes
5. View the audit trail for each alert

## 5. Generate Reports

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

