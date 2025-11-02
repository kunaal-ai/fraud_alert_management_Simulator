"""Generate synthetic transaction data for testing."""
import pandas as pd
import random
from datetime import datetime, timedelta
import string
import os


def generate_transaction_id():
    """Generate a unique transaction ID."""
    return 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def generate_customer_id():
    """Generate a customer ID."""
    return 'CUST' + ''.join(random.choices(string.digits, k=8))


def generate_device_id():
    """Generate a device ID."""
    return 'DEV' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def generate_ip_address():
    """Generate a random IP address."""
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"


# Merchant data
MERCHANTS = [
    "Amazon", "Walmart", "Target", "Best Buy", "Home Depot", "Costco",
    "Starbucks", "McDonald's", "Shell", "Chevron", "Uber", "Lyft",
    "Apple Store", "Microsoft Store", "Netflix", "Spotify", "Airbnb",
    "Booking.com", "Expedia", "Delta Airlines", "United Airlines",
    "Nike", "Adidas", "Zara", "H&M", "Whole Foods", "Trader Joe's"
]

CITIES = [
    ("New York", "USA"), ("Los Angeles", "USA"), ("Chicago", "USA"),
    ("Houston", "USA"), ("Miami", "USA"), ("San Francisco", "USA"),
    ("Toronto", "Canada"), ("London", "UK"), ("Paris", "France"),
    ("Berlin", "Germany"), ("Tokyo", "Japan"), ("Sydney", "Australia"),
    ("Dubai", "UAE"), ("Singapore", "Singapore"), ("Hong Kong", "China")
]

MCC_CODES = ["5411", "5812", "5814", "5912", "5999", "5311", "5331", "5399"]
# High-risk MCC codes for suspicious merchant rule
HIGH_RISK_MCC_CODES = ["7995", "7273", "5967", "5912"]


def generate_transactions(num_transactions=500, days_back=30):
    """Generate synthetic transaction data."""
    transactions = []
    customer_pools = {generate_customer_id(): {
        'device_id': generate_device_id(),
        'last_location': random.choice(CITIES),
        'last_transaction_time': None,
        'transaction_count': 0
    } for _ in range(100)}
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    # Track transactions per customer for velocity detection
    customer_transaction_times = {}
    
    # Create some high-risk customers with multiple patterns
    high_risk_customers = list(customer_pools.keys())[:20]  # First 20 customers as high-risk
    
    for i in range(num_transactions):
        # Create intentional fraud patterns for variety of severities
        # 10% - CRITICAL scenarios (multiple high-risk patterns)
        # 15% - HIGH scenarios (2-3 risk patterns)
        # 25% - MEDIUM scenarios (2 moderate patterns)
        # 50% - LOW scenarios (normal transactions, maybe 1 pattern)
        
        fraud_scenario = random.random()
        
        # Select a customer (some customers will have multiple transactions)
        customer_id = random.choice(list(customer_pools.keys()))
        customer = customer_pools[customer_id]
        is_high_risk_customer = customer_id in high_risk_customers
        
        # Generate transaction date (more recent transactions are more common)
        days_ago = random.choices(
            range(days_back),
            weights=[1.5 ** (days_back - d) for d in range(days_back)]
        )[0]
        
        # Track velocity for high-risk customers
        if customer_id not in customer_transaction_times:
            customer_transaction_times[customer_id] = []
        
        # CRITICAL scenario: High amount + Velocity + Geo jump + Unusual time
        if fraud_scenario < 0.10:
            amount = random.uniform(6000, 12000)  # High amount
            # Create rapid transactions for velocity
            if len(customer_transaction_times[customer_id]) > 0:
                last_txn_time = max(customer_transaction_times[customer_id])
                transaction_date = last_txn_time + timedelta(minutes=random.randint(5, 30))
            else:
                base_time = start_date + timedelta(days=days_ago)
                transaction_date = base_time.replace(hour=random.randint(2, 4))  # Unusual time (2-5 AM)
            
            city, country = random.choice(CITIES)  # Geo jump
            customer['last_location'] = (city, country)
            device_id = customer['device_id']
            mcc_code = random.choice(HIGH_RISK_MCC_CODES)  # Suspicious merchant
        
        # HIGH scenario: High amount + Velocity OR High amount + Geo jump + Unusual time
        elif fraud_scenario < 0.25:
            amount = random.uniform(5500, 10000)  # High amount
            if random.random() < 0.5:
                # Velocity pattern
                if len(customer_transaction_times[customer_id]) > 0:
                    last_txn_time = max(customer_transaction_times[customer_id])
                    transaction_date = last_txn_time + timedelta(minutes=random.randint(10, 45))
                else:
                    transaction_date = start_date + timedelta(days=days_ago, hours=random.randint(10, 20))
                city, country = customer['last_location']
            else:
                # Geo jump + Unusual time
                transaction_date = start_date + timedelta(days=days_ago)
                transaction_date = transaction_date.replace(hour=random.randint(2, 4))  # Unusual time
                city, country = random.choice(CITIES)  # Geo jump
                customer['last_location'] = (city, country)
            device_id = customer['device_id']
            mcc_code = random.choice(MCC_CODES)
        
        # MEDIUM scenario: Need 2 rules to reach 40+ points
        # Options: High amount + Unusual time (40), Velocity + Geo jump (45), High amount + Suspicious merchant (45)
        elif fraud_scenario < 0.50:
            base_time = start_date + timedelta(days=days_ago)
            scenario_type = random.random()
            
            if scenario_type < 0.33:
                # High amount + Unusual time = 30 + 10 = 40 (MEDIUM)
                amount = random.uniform(5500, 8000)  # High amount
                transaction_date = base_time.replace(hour=random.randint(2, 4))  # Unusual time
                city, country = customer['last_location']
                mcc_code = random.choice(MCC_CODES)
            elif scenario_type < 0.66:
                # Velocity + Geo jump = 25 + 20 = 45 (MEDIUM)
                amount = random.uniform(1000, 4500)  # Not high amount
                if len(customer_transaction_times[customer_id]) > 0:
                    last_txn_time = max(customer_transaction_times[customer_id])
                    transaction_date = last_txn_time + timedelta(minutes=random.randint(15, 45))
                else:
                    transaction_date = base_time.replace(hour=random.randint(10, 20))
                city, country = random.choice(CITIES)  # Geo jump
                customer['last_location'] = (city, country)
                mcc_code = random.choice(MCC_CODES)
            else:
                # High amount + Suspicious merchant = 30 + 15 = 45 (MEDIUM)
                amount = random.uniform(5500, 8000)  # High amount
                transaction_date = base_time.replace(hour=random.randint(10, 22))
                city, country = customer['last_location']
                mcc_code = random.choice(HIGH_RISK_MCC_CODES)  # Suspicious merchant
            
            device_id = customer['device_id']
        
        # LOW scenario: Normal transaction patterns
        else:
            if random.random() < 0.85:
                device_id = customer['device_id']
            else:
                device_id = generate_device_id()
            
            if random.random() < 0.75:
                city, country = customer['last_location']
            else:
                city, country = random.choice(CITIES)
                customer['last_location'] = (city, country)
            
            if random.random() < 0.15:
                amount = random.uniform(5000, 15000)  # High amount (single rule)
            elif random.random() < 0.3:
                amount = random.uniform(1000, 5000)
            else:
                amount = random.uniform(10, 1000)
            
            transaction_date = start_date + timedelta(days=days_ago, hours=random.randint(0, 23))
            mcc_code = random.choice(MCC_CODES)
        
        # Velocity tracking
        customer_transaction_times[customer_id].append(transaction_date)
        if len(customer_transaction_times[customer_id]) > 10:
            customer_transaction_times[customer_id] = customer_transaction_times[customer_id][-10:]
        
        customer['transaction_count'] += 1
        customer['last_transaction_time'] = transaction_date
        
        transaction = {
            'transaction_id': generate_transaction_id(),
            'customer_id': customer_id,
            'merchant': random.choice(MERCHANTS),
            'amount': round(amount, 2),
            'currency': 'USD',
            'transaction_date': transaction_date,
            'card_type': random.choice(['Visa', 'Mastercard', 'Amex', 'Discover']),
            'device_id': device_id,
            'ip_address': generate_ip_address(),
            'country': country,
            'city': city,
            'mcc_code': mcc_code,
            'status': 'completed'
        }
        
        transactions.append(transaction)
    
    return pd.DataFrame(transactions)


def save_transactions_to_csv(df, filepath='data/transactions.csv'):
    """Save transactions to CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(df)} transactions to {filepath}")
    return filepath


if __name__ == '__main__':
    # Generate and save sample data
    print("Generating synthetic transaction data...")
    df = generate_transactions(num_transactions=500, days_back=30)
    save_transactions_to_csv(df)

