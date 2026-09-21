import pandas as pd
import numpy as np
from datetime import datetime

print("🧹 Starting data cleaning process...")
print("="*60)

# Load data
df = pd.read_csv('data/raw/nvd_vulnerabilities.csv')
print(f"Initial data: {len(df):,} rows")

# ============================================================
# Step 1: Remove rows without CVSS score
# ============================================================
print("\n📌 Step 1: Removing rows without CVSS score...")
df = df[df['cvss_base_score'] > 0]
print(f"   Remaining: {len(df):,} rows")

# ============================================================
# Step 2: Remove duplicates
# ============================================================
print("\n📌 Step 2: Removing duplicate entries...")
before = len(df)
df = df.drop_duplicates(subset=['cve_id'])
removed = before - len(df)
print(f"   Removed: {removed:,} rows")
print(f"   Remaining: {len(df):,} rows")

# ============================================================
# Step 3: Handle missing values
# ============================================================
print("\n📌 Step 3: Handling missing values...")

# Show missing values before fixing
print("\n   Missing values before fixing:")
missing_before = df.isnull().sum()
for col in missing_before[missing_before > 0].index:
    print(f"     - {col}: {missing_before[col]} rows")

# Replace UNKNOWN values
print("\n   Replacing UNKNOWN values...")
replacements = {
    'attack_vector': 'NETWORK',
    'attack_complexity': 'LOW',
    'privileges_required': 'NONE',
    'user_interaction': 'NONE'
}

for col, default_value in replacements.items():
    if col in df.columns:
        df[col] = df[col].replace('UNKNOWN', default_value)
        print(f"     ✓ {col} → {default_value}")

# ============================================================
# Step 4: Create new columns
# ============================================================
print("\n📌 Step 4: Creating new columns...")

# Convert published_date to datetime
df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

# Calculate days since published
df['days_since_published'] = (pd.Timestamp.now() - df['published_date']).dt.days

# Remove rows with negative days_since_published (data errors)
df = df[df['days_since_published'] >= 0]

print(f"   ✓ Created column 'days_since_published'")
print(f"   Remaining: {len(df):,} rows")

# ============================================================
# Step 5: Check for outliers
# ============================================================
print("\n📌 Step 5: Checking for outliers...")

# CVSS score must be between 0-10
invalid_cvss = df[(df['cvss_base_score'] < 0) | (df['cvss_base_score'] > 10)]
print(f"   Invalid CVSS scores: {len(invalid_cvss)} rows")
df = df[(df['cvss_base_score'] >= 0) & (df['cvss_base_score'] <= 10)]

# Exploitability score must be between 0-10
invalid_exploit = df[(df['exploitability_score'] < 0) | (df['exploitability_score'] > 10)]
print(f"   Invalid Exploitability scores: {len(invalid_exploit)} rows")
df = df[(df['exploitability_score'] >= 0) & (df['exploitability_score'] <= 10)]

# Impact score must be between 0-10
invalid_impact = df[(df['impact_score'] < 0) | (df['impact_score'] > 10)]
print(f"   Invalid Impact scores: {len(invalid_impact)} rows")
df = df[(df['impact_score'] >= 0) & (df['impact_score'] <= 10)]

print(f"   Remaining: {len(df):,} rows")

# ============================================================
# Step 6: Sort data
# ============================================================
print("\n📌 Step 6: Sorting data...")
df = df.sort_values('published_date', ascending=False)
df = df.reset_index(drop=True)
print("   ✓ Sorted by publish date (newest first)")

# ============================================================
# Save cleaned data
# ============================================================
output_file = 'data/processed/cleaned_vulnerabilities.csv'
df.to_csv(output_file, index=False)

print("\n" + "="*60)
print("✨ Data cleaning completed!")
print("="*60)
print(f"\n📊 Final dataset summary:")
print(f"   Total rows: {len(df):,}")
print(f"   Total columns: {len(df.columns)}")
print(f"   File saved to: {output_file}")

print(f"\n📈 CVSS Score statistics:")
print(f"   Min: {df['cvss_base_score'].min():.1f}")
print(f"   Max: {df['cvss_base_score'].max():.1f}")
print(f"   Mean: {df['cvss_base_score'].mean():.2f}")

print(f"\n⚠️  Severity distribution:")
severity_dist = df['cvss_severity'].value_counts()
for severity, count in severity_dist.items():
    percentage = (count / len(df)) * 100
    print(f"   {severity:10s}: {count:6,} ({percentage:5.2f}%)")

print("\n✅ Ready for next step: Feature Engineering!")