import pandas as pd
import numpy as np

print("🔄 Converting Kaggle data format...")

# Load Kaggle data
df = pd.read_csv('data/raw/nvd_vulnerabilities.csv')
print(f"Loaded {len(df)} records")

# Rename and create required columns
df_converted = pd.DataFrame()

# Basic columns
df_converted['cve_id'] = df.iloc[:, 0]  # First column is CVE ID
df_converted['description'] = df['summary'].fillna('')
df_converted['published_date'] = df['pub_date']
df_converted['cwe_id'] = df['cwe_code'].fillna('N/A').astype(str)

# CVSS score
df_converted['cvss_base_score'] = pd.to_numeric(df['cvss'], errors='coerce').fillna(0)

# Create severity from CVSS score
def get_severity(score):
    if score >= 9.0:
        return 'CRITICAL'
    elif score >= 7.0:
        return 'HIGH'
    elif score >= 4.0:
        return 'MEDIUM'
    elif score > 0:
        return 'LOW'
    else:
        return 'NONE'

df_converted['cvss_severity'] = df_converted['cvss_base_score'].apply(get_severity)

# Estimate exploitability and impact (based on CVSS score)
df_converted['exploitability_score'] = (df_converted['cvss_base_score'] * 0.4).round(1)
df_converted['impact_score'] = (df_converted['cvss_base_score'] * 0.6).round(1)

# Create attack vector based on available data
df_converted['attack_vector'] = 'NETWORK'  # Most common
df_converted['attack_complexity'] = 'LOW'
df_converted['privileges_required'] = 'NONE'
df_converted['user_interaction'] = 'NONE'

# Remove rows without CVSS score
df_converted = df_converted[df_converted['cvss_base_score'] > 0]

print(f"\n✅ Converted {len(df_converted)} valid records")

# Save
df_converted.to_csv('data/raw/nvd_vulnerabilities.csv', index=False)

print(f"\n📊 Sample data:")
print(df_converted.head())
print(f"\n💾 Saved to: data/raw/nvd_vulnerabilities.csv")