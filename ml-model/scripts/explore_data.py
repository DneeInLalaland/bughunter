import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
df = pd.read_csv('data/raw/nvd_vulnerabilities.csv')

print("\n" + "="*60)
print("📊 Basic Information")
print("="*60)

# 1. Dataset size
print(f"\n🔢 Dataset size: {df.shape[0]:,} rows × {df.shape[1]} columns")

# 2. Display first 5 rows
print("\n👀 Sample data (first 5 rows):")
print(df.head())

# 3. Data types
print("\n📋 Data types for each column:")
print(df.dtypes)

# 4. Missing values
print("\n🕳️  Missing values:")
missing = df.isnull().sum()
missing_percent = (missing / len(df)) * 100
missing_df = pd.DataFrame({
    'Missing Count': missing,
    'Percentage': missing_percent
})
print(missing_df[missing_df['Missing Count'] > 0])

# 5. Basic statistics
print("\n📈 Basic statistics:")
print(df.describe())

# 6. CVSS Score distribution
print("\n🎯 CVSS Base Score distribution:")
print(df['cvss_base_score'].describe())

# 7. Severity distribution
print("\n⚠️  Severity Level distribution:")
print(df['cvss_severity'].value_counts())

print("\n" + "="*60)
print("📊 Creating visualizations...")
print("="*60)
# Create 4 plots
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Plot 1: CVSS Score Distribution
axes[0, 0].hist(df['cvss_base_score'], bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('CVSS Base Score')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of CVSS Scores')
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Severity Distribution
severity_counts = df['cvss_severity'].value_counts()
axes[0, 1].bar(severity_counts.index, severity_counts.values, 
               color=['red', 'orange', 'yellow', 'green', 'gray'])
axes[0, 1].set_xlabel('Severity Level')
axes[0, 1].set_ylabel('Count')
axes[0, 1].set_title('Number of Vulnerabilities by Severity')
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# Plot 3: Attack Vector Distribution
attack_vector_counts = df['attack_vector'].value_counts()
axes[1, 0].pie(attack_vector_counts.values, labels=attack_vector_counts.index, 
               autopct='%1.1f%%', startangle=90)
axes[1, 0].set_title('Attack Vector Distribution')

# Plot 4: Exploitability vs Impact Score
axes[1, 1].scatter(df['exploitability_score'], df['impact_score'], 
                   alpha=0.3, s=10)
axes[1, 1].set_xlabel('Exploitability Score')
axes[1, 1].set_ylabel('Impact Score')
axes[1, 1].set_title('Exploitability vs Impact Score')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/exploration_plots.png', dpi=300, bbox_inches='tight')
print("✅ Plots saved: data/exploration_plots.png")

plt.show()

print("\n✨ Data exploration completed!")