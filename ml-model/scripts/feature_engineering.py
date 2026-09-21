import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

class FeatureEngineer:
    """
    Create and transform features for ML model
    """
    
    def __init__(self):
        self.label_encoders = {}
    
    def create_features(self, df):
        """
        Create all features
        
        Args:
            df (DataFrame): Vulnerability data
            
        Returns:
            DataFrame: Data with new features
        """
        df = df.copy()
        
        print("🔧 Starting feature engineering...")
        print("="*60)
        
        # 1. Encode categorical variables
        print("\n📌 Step 1: Encoding categorical variables...")
        df = self._encode_categorical(df)
        
        # 2. Create derived features
        print("\n📌 Step 2: Creating derived features...")
        df = self._create_derived_features(df)
        
        # 3. Create target variable (risk_level)
        print("\n📌 Step 3: Creating target variable (risk_level)...")
        df = self._create_target(df)
        
        print("\n✨ Feature engineering completed!")
        return df
    
    def _encode_categorical(self, df):
        """
        Convert categorical variables to numeric values
        
        Example: 'CRITICAL' → 0, 'HIGH' → 1
        """
        categorical_cols = [
            'cvss_severity',
            'attack_vector',
            'attack_complexity',
            'privileges_required',
            'user_interaction'
        ]
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Display mapping
        print("\n   Encoding mappings:")
        for col in categorical_cols:
            classes = self.label_encoders[col].classes_
            print(f"\n   {col}:")
            for i, cls in enumerate(classes):
                print(f"     {cls:20s} → {i}")
        
        return df
    
    def _create_derived_features(self, df):
        """
        Create new features from existing data
        """
        # Feature 1: CVSS Combined Score
        # Combine base_score, exploitability, and impact into one score
        df['cvss_combined'] = (
            df['cvss_base_score'] * 0.6 +
            df['exploitability_score'] * 0.2 +
            df['impact_score'] * 0.2
        )
        print("   ✓ cvss_combined (combined CVSS scores)")
        
        # Feature 2: Attack Ease Score
        # Calculate how easy it is to exploit
        
        # Attack Vector Score
        attack_vector_map = {
            0: 1,  # Adjacent = harder
            1: 3,  # Network = easiest
            2: 2   # Local = medium (if exists)
        }
        attack_vector_score = df['attack_vector_encoded'].map(attack_vector_map).fillna(1)
        
        # Attack Complexity Score
        complexity_map = {
            0: 1,  # High = harder
            1: 2   # Low = easier
        }
        complexity_score = df['attack_complexity_encoded'].map(complexity_map).fillna(1)
        
        # Privileges Required Score
        privilege_map = {
            0: 1,  # High = requires high privileges (harder)
            1: 2,  # Low = requires low privileges (medium)
            2: 3   # None = no privileges needed (easiest)
        }
        privilege_score = df['privileges_required_encoded'].map(privilege_map).fillna(1)
        
        # Combine into Attack Ease Score
        df['attack_ease_score'] = (
            attack_vector_score * 0.4 +
            complexity_score * 0.3 +
            privilege_score * 0.3
        )
        print("   ✓ attack_ease_score (ease of exploitation)")
        
        # Feature 3: Public Exposure
        # Vulnerabilities that are Network-accessible and require no privileges = high risk
        df['public_exposure'] = (
            (df['attack_vector'] == 'NETWORK') &
            (df['privileges_required'] == 'NONE')
        ).astype(int)
        print("   ✓ public_exposure (risk of external attacks)")
        
        # Feature 4: Age Factor
        # Older vulnerabilities = discovered long ago = might have exploits available
        max_days = df['days_since_published'].max()
        df['age_factor'] = df['days_since_published'] / max_days
        print("   ✓ age_factor (vulnerability age)")
        
        # Feature 5: Severity Score
        # Convert severity to numeric score
        severity_map = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1,
            'NONE': 0
        }
        df['severity_score'] = df['cvss_severity'].map(severity_map)
        print("   ✓ severity_score (severity rating)")
        
        return df
    
    def _create_target(self, df):
        """
        Create target variable: risk_level
        
        Risk level calculated from:
        - CVSS score (60%)
        - Attack ease (20%)
        - Age factor (10%)
        - Public exposure (10%)
        """
        
        # Normalize all components to 0-10 scale
        cvss_normalized = df['cvss_base_score']  # already 0-10
        attack_ease_normalized = (df['attack_ease_score'] / df['attack_ease_score'].max()) * 10
        age_normalized = df['age_factor'] * 10
        public_exposure_normalized = df['public_exposure'] * 10
        
        # Calculate risk score
        df['risk_score'] = (
            cvss_normalized * 0.6 +
            attack_ease_normalized * 0.2 +
            age_normalized * 0.1 +
            public_exposure_normalized * 0.1
        )
        
        # Convert risk score to categorical risk_level
        def categorize_risk(score):
            if score < 3:
                return 'Low'
            elif score < 5:
                return 'Medium'
            elif score < 7:
                return 'High'
            else:
                return 'Critical'
        
        df['risk_level'] = df['risk_score'].apply(categorize_risk)
        
        print("\n   Risk level distribution:")
        risk_dist = df['risk_level'].value_counts()
        for level, count in risk_dist.items():
            percentage = (count / len(df)) * 100
            print(f"     {level:10s}: {count:6,} ({percentage:5.2f}%)")
        
        return df
    
    def get_feature_columns(self):
        """
        Return list of feature columns for training
        """
        return [
            'cvss_base_score',
            'exploitability_score',
            'impact_score',
            'cvss_severity_encoded',
            'attack_vector_encoded',
            'attack_complexity_encoded',
            'privileges_required_encoded',
            'user_interaction_encoded',
            'cvss_combined',
            'attack_ease_score',
            'public_exposure',
            'age_factor',
            'severity_score'
        ]


# Main execution
if __name__ == "__main__":
    print("🚀 Feature Engineering Pipeline")
    print("="*60)
    
    # Load cleaned data
    print("\n📂 Loading data...")
    df = pd.read_csv('data/processed/cleaned_vulnerabilities.csv')
    print(f"   Data: {len(df):,} rows × {len(df.columns)} columns")
    
    # Feature engineering
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df)
    
    # Save
    output_file = 'data/processed/features.csv'
    df_features.to_csv(output_file, index=False)
    
    print("\n" + "="*60)
    print("✅ Data saved successfully!")
    print("="*60)
    print(f"   File: {output_file}")
    print(f"   Total rows: {len(df_features):,}")
    print(f"   Total columns: {len(df_features.columns)}")
    
    # Display feature columns
    feature_cols = engineer.get_feature_columns()
    print(f"\n📊 Features for model training ({len(feature_cols)} features):")
    for i, col in enumerate(feature_cols, 1):
        print(f"   {i:2d}. {col}")
    
    print("\n🎉 Ready for next step: Model Training!")