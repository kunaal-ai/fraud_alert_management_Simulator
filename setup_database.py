#!/usr/bin/env python3
"""Setup script to initialize database and load sample data."""
from fraud_alert_system.database import create_database
from fraud_alert_system.data_generator import generate_transactions, save_transactions_to_csv
from fraud_alert_system.ingestion import load_transactions_from_csv
from fraud_alert_system.fraud_engine import FraudDetectionEngine

import os

def main():
    """Setup the fraud alert system."""
    print("=" * 60)
    print("Fraud Alert Management System - Setup")
    print("=" * 60)
    
    # Step 1: Create database
    print("\n[1/4] Creating database...")
    create_database()
    print("✓ Database created successfully")
    
    # Step 2: Generate sample transactions
    print("\n[2/4] Generating sample transaction data...")
    df = generate_transactions(num_transactions=500, days_back=30)
    csv_path = save_transactions_to_csv(df, 'data/transactions.csv')
    print(f"✓ Generated {len(df)} transactions")
    
    # Step 3: Load transactions into database
    print("\n[3/4] Loading transactions into database...")
    load_transactions_from_csv(csv_path)
    print("✓ Transactions loaded")
    
    # Step 4: Run fraud detection engine
    print("\n[4/4] Running fraud detection engine...")
    engine = FraudDetectionEngine()
    try:
        alerts_generated = engine.process_transactions()
        print(f"✓ Generated {alerts_generated} fraud alerts")
    finally:
        engine.close()
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now run the dashboard with:")
    print("  streamlit run app.py")
    print("=" * 60)

if __name__ == '__main__':
    main()

