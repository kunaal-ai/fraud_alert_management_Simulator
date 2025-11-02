# Fraud Case Scenarios

This directory contains sample fraud case scenarios in JSON format. Each scenario demonstrates different types of fraud patterns and alert triggers.

## Available Scenarios

### Case 1: High Amount + Velocity (`case_1_high_amount_velocity.json`)
- **Alert Types**: HIGH_AMOUNT, VELOCITY
- **Expected Severity**: CRITICAL
- **Description**: Demonstrates rapid-fire high-value transactions, typical of card testing or fraudulent spending sprees
- **Key Features**:
  - 6 transactions all exceeding $5,000
  - All within 1 hour
  - Same device and IP address
  - Multiple high-value merchants

### Case 2: Geographic Jump (`case_2_geo_jump.json`)
- **Alert Type**: GEO_JUMP
- **Expected Severity**: HIGH
- **Description**: Shows impossible travel patterns where transactions occur in distant locations within short time frames
- **Key Features**:
  - New York → Los Angeles → San Francisco in under 3 hours
  - Physically impossible travel distances
  - Same device ID across all locations

### Case 3: Device Sharing + Unusual Time (`case_3_device_sharing_unusual_time.json`)
- **Alert Types**: DEVICE_SHARING, UNUSUAL_TIME, SUSPICIOUS_MERCHANT
- **Expected Severity**: MEDIUM to HIGH
- **Description**: Demonstrates device sharing fraud with unusual transaction times
- **Key Features**:
  - 4 different customers using same device
  - Transactions between 2-5 AM
  - All at high-risk gaming merchant (MCC 7995)
  - Potential fraud ring pattern

## Usage

These scenario files can be used to:
1. Test fraud detection rules
2. Generate sample alerts for demonstration
3. Train analysts on different fraud patterns
4. Validate alert generation logic

To load a scenario:
1. Parse the JSON file
2. Import transactions into the database using the ingestion module
3. Run the fraud detection engine to generate alerts
4. Verify that expected rules are triggered

## Scenario Format

Each scenario file contains:
- `scenario_name`: Descriptive name
- `description`: What the scenario demonstrates
- `alert_type`: Expected alert types
- `expected_severity`: Expected severity level
- `expected_rules`: List of rules that should trigger
- `transactions`: Array of transaction objects matching database schema
- `investigation_notes`: Guidance for analysts reviewing these alerts



