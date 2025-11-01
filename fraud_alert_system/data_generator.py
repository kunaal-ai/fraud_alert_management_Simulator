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
    
    for i in range(num_transactions):
        # Select a customer (some customers will have multiple transactions)
        customer_id = random.choice(list(customer_pools.keys()))
        customer = customer_pools[customer_id]
        
        # Generate transaction date (more recent transactions are more common)
        days_ago = random.choices(
            range(days_back),
            weights=[1.5 ** (days_back - d) for d in range(days_back)]
        )[0]
        transaction_date = start_date + timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Sometimes use same device, sometimes different (for device sharing detection)
        if random.random() < 0.85:
            device_id = customer['device_id']
        else:
            device_id = generate_device_id()
        
        # Location - sometimes same city, sometimes jump (for geo-jump detection)
        if random.random() < 0.75:
            city, country = customer['last_location']
        else:
            city, country = random.choice(CITIES)
            customer['last_location'] = (city, country)
        
        # Amount - sometimes high (for amount-based rules)
        if random.random() < 0.15:
            amount = random.uniform(5000, 15000)
        elif random.random() < 0.3:
            amount = random.uniform(1000, 5000)
        else:
            amount = random.uniform(10, 1000)
        
        # Velocity - some customers will have many transactions
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
            'mcc_code': random.choice(MCC_CODES),
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

