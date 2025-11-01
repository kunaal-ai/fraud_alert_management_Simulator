"""Data ingestion script to load CSV into database."""
import pandas as pd
from sqlalchemy.exc import IntegrityError
from fraud_alert_system.database import get_session, Transaction
import sys
import os


def load_transactions_from_csv(csv_path):
    """Load transactions from CSV file into database."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    session = get_session()
    loaded = 0
    skipped = 0
    
    try:
        for _, row in df.iterrows():
            try:
                transaction = Transaction(
                    transaction_id=row['transaction_id'],
                    customer_id=row['customer_id'],
                    merchant=row['merchant'],
                    amount=float(row['amount']),
                    currency=row.get('currency', 'USD'),
                    transaction_date=row['transaction_date'],
                    card_type=row.get('card_type'),
                    device_id=row.get('device_id'),
                    ip_address=row.get('ip_address'),
                    country=row.get('country'),
                    city=row.get('city'),
                    mcc_code=row.get('mcc_code'),
                    status=row.get('status', 'completed')
                )
                session.add(transaction)
                session.commit()
                loaded += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
                continue
        
        print(f"✓ Loaded {loaded} transactions into database")
        if skipped > 0:
            print(f"⚠ Skipped {skipped} duplicate transactions")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error loading transactions: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'data/transactions.csv'
    load_transactions_from_csv(csv_path)

