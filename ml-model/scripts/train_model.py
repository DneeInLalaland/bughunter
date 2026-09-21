import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

class ModelTrainer:
    """
    Train ML model for risk prediction
    """
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.label_mapping = {
            'Low': 0,
            'Medium': 1,
            'High': 2,
            'Critical': 3
        }
    
    def prepare_data(self, df, feature_columns):
        """
        Prepare data for training
        
        Args:
            df (DataFrame): Data with features
            feature_columns (list): List of feature column names
            
        Returns:
            tuple: X_train, X_val, X_test, y_train, y_val, y_test
        """
        self.feature_columns = feature_columns
        
        print("📊 Preparing data...")
        
        # Select only feature columns
        X = df[feature_columns]
        
        # Target variable (convert to numeric)
        y = df['risk_level'].map(self.label_mapping)
        
        # Split data: 70% train, 15% validation, 15% test
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )
        
        print(f"\n   Training set:   {len(X_train):,} samples ({len(X_train)/len(X)*100:.1f}%)")
        print(f"   Validation set: {len(X_val):,} samples ({len(X_val)/len(X)*100:.1f}%)")
        print(f"   Test set:       {len(X_test):,} samples ({len(X_test)/len(X)*100:.1f}%)")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train(self, X_train, y_train):
        """
        Train Random Forest model
        
        Args:
            X_train: Training features
            y_train: Training labels
        """
        print("\n🤖 Training Random Forest Model...")
        print("   (This may take 1-3 minutes)")
        print("="*60)
        
        self.model = RandomForestClassifier(
            n_estimators=100,        # Number of trees
            max_depth=20,            # Maximum depth of each tree
            min_samples_split=5,     # Minimum samples required to split
            min_samples_leaf=2,      # Minimum samples in leaf node
            random_state=42,
            n_jobs=-1,               # Use all CPU cores
            verbose=1                # Show progress
        )
        
        self.model.fit(X_train, y_train)
        
        print("\n✅ Training completed!")
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            float: Accuracy score
        """
        print("\n📈 Evaluating model...")
        print("="*60)
        
        # Predict
        y_pred = self.model.predict(X_test)
        
        # Accuracy
        accuracy = accuracy_score(y_test, y_pred)
        print(f"\n🎯 Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        if accuracy >= 0.90:
            print("   ✅ Target achieved! (>90%)")
        else:
            print("   ⚠️  Below 90% target")
        
        # Classification report
        reverse_label_mapping = {v: k for k, v in self.label_mapping.items()}
        risk_levels = sorted(set([reverse_label_mapping.get(i, 'Unknown') for i in y_test.unique()]))
        print(f"\n📊 Classification Report:")
        print("-"*60)
        print(classification_report(y_test, y_pred, target_names=risk_levels))
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=risk_levels,
                    yticklabels=risk_levels,
                    cbar_kws={'label': 'Count'})
        plt.xlabel('Predicted', fontsize=12)
        plt.ylabel('Actual', fontsize=12)
        plt.title('Confusion Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('models/confusion_matrix.png', dpi=300, bbox_inches='tight')
        print("   ✓ Plot saved: models/confusion_matrix.png")
        plt.show()
        
        return accuracy
    
    def cross_validate(self, X, y, cv=5):
        """
        Cross-validation to check model stability
        
        Args:
            X: Features
            y: Labels
            cv: Number of folds
        """
        print(f"\n🔄 Performing {cv}-Fold Cross-Validation...")
        print("   (This may take 2-5 minutes)")
        
        scores = cross_val_score(self.model, X, y, cv=cv, scoring='accuracy')
        
        print(f"\n   Cross-validation scores: {[f'{s:.4f}' for s in scores]}")
        print(f"   Mean accuracy: {scores.mean():.4f} (±{scores.std() * 2:.4f})")
        
        if scores.std() < 0.02:
            print("   ✅ Model is highly stable!")
        else:
            print("   ⚠️  Model might have high variance")
    
    def feature_importance(self):
        """
        Display feature importance
        """
        if self.model is None:
            print("❌ Model not trained yet!")
            return
        
        print("\n🔍 Feature Importance:")
        print("="*60)
        
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\nTop 10 Features:")
        for i in range(min(10, len(self.feature_columns))):
            idx = indices[i]
            print(f"   {i+1:2d}. {self.feature_columns[idx]:30s}: {importances[idx]:.4f}")
        
        # Plot
        plt.figure(figsize=(12, 8))
        plt.title("Feature Importance", fontsize=14, fontweight='bold')
        plt.bar(range(len(importances)), importances[indices], alpha=0.7)
        plt.xticks(range(len(importances)),
                  [self.feature_columns[i] for i in indices],
                  rotation=45, ha='right')
        plt.xlabel('Features', fontsize=12)
        plt.ylabel('Importance', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('models/feature_importance.png', dpi=300, bbox_inches='tight')
        print("\n   ✓ Plot saved: models/feature_importance.png")
        plt.show()
    
    def save_model(self, filepath='models/risk_model.pkl'):
        """
        Save model to file
        """
        if self.model is None:
            print("❌ Model not trained yet!")
            return
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'label_mapping': self.label_mapping
        }
        
        joblib.dump(model_data, filepath)
        print(f"\n💾 Model saved: {filepath}")
    
    def load_model(self, filepath='models/risk_model.pkl'):
        """
        Load model from file
        """
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.label_mapping = model_data['label_mapping']
        print(f"📂 Model loaded from: {filepath}")


# Main execution
if __name__ == "__main__":
    print("🚀 ML Model Training Pipeline")
    print("="*60)
    
    # Load feature data
    print("\n📂 Loading data...")
    df = pd.read_csv('data/processed/features.csv')
    print(f"   Data: {len(df):,} rows")
    
    # Feature columns
    feature_columns = [
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
    
    # Create trainer
    trainer = ModelTrainer()
    
    # Prepare data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.prepare_data(
        df, feature_columns
    )
    
    # Train
    trainer.train(X_train, y_train)
    
    # Evaluate
    accuracy = trainer.evaluate(X_test, y_test)
    
    # Feature importance
    trainer.feature_importance()
    
    # Cross-validation
    trainer.cross_validate(X_train, y_train, cv=5)
    
    # Save model
    trainer.save_model('models/risk_model.pkl')
    
    print("\n" + "="*60)
    print("🎉 Training Pipeline Completed!")
    print("="*60)
    print(f"   Final Test Accuracy: {accuracy*100:.2f}%")
    print(f"   Model saved at: models/risk_model.pkl")
    print("\n✅ Ready for next step: Explainable AI!")