from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import os

app = Flask(__name__)
CORS(app)

# Load model
MODEL_PATH = 'models/risk_model.pkl'
model_data = joblib.load(MODEL_PATH)
model = model_data['model']
feature_columns = model_data['feature_columns']
label_mapping = model_data['label_mapping']
reverse_label_mapping = {v: k for k, v in label_mapping.items()}

# Human-readable feature names for SHAP explanations
FEATURE_DESCRIPTIONS = {
    'cvss_base_score': 'CVSS Base Score',
    'exploitability_score': 'Exploitability Score',
    'impact_score': 'Impact Score',
    'cvss_severity_encoded': 'CVSS Severity Level',
    'attack_vector_encoded': 'Attack Vector',
    'attack_complexity_encoded': 'Attack Complexity',
    'privileges_required_encoded': 'Privileges Required',
    'user_interaction_encoded': 'User Interaction Required',
    'cvss_combined': 'Combined CVSS Score',
    'attack_ease_score': 'Attack Ease Score',
    'public_exposure': 'Public Exposure',
    'age_factor': 'Vulnerability Age',
    'severity_score': 'Severity Score'
}

print("✅ ML Model loaded successfully!")


@app.route('/')
def home():
    """API info page"""
    return jsonify({
        'name': 'ML Risk Scorer API',
        'version': '1.0',
        'model': 'Random Forest',
        'accuracy': '93.42%',
        'endpoints': {
            '/predict': 'POST - Predict risk level for a single vulnerability',
            '/explain': 'POST - Get SHAP explanation for prediction',
            '/batch-predict': 'POST - Predict risk for multiple vulnerabilities',
            '/health': 'GET - Check API health',
            '/features': 'GET - List required features'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,
        'features_count': len(feature_columns)
    })


@app.route('/features', methods=['GET'])
def get_features():
    """Return list of required features"""
    return jsonify({
        'required_features': feature_columns,
        'count': len(feature_columns)
    })


@app.route('/predict', methods=['POST'])
def predict():
    """Predict risk level for a single vulnerability"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        df = pd.DataFrame([data])
        
        missing_features = set(feature_columns) - set(df.columns)
        if missing_features:
            return jsonify({
                'error': f'Missing features: {list(missing_features)}',
                'required_features': feature_columns
            }), 400
        
        X = df[feature_columns]
        
        prediction = model.predict(X)[0]
        prediction_proba = model.predict_proba(X)[0]
        
        risk_level = reverse_label_mapping.get(prediction, 'Unknown')
        confidence = float(max(prediction_proba))
        
        probabilities = {}
        for label_idx, prob in enumerate(prediction_proba):
            if label_idx in reverse_label_mapping:
                probabilities[reverse_label_mapping[label_idx]] = float(prob)
        
        return jsonify({
            'risk_level': risk_level,
            'confidence': confidence,
            'probabilities': probabilities,
            'input_features': data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/explain', methods=['POST'])
def explain():
    """
    Get SHAP-like explanation for why a vulnerability has its risk level.
    Uses feature importance from Random Forest to explain prediction.
    
    Request body: same as /predict
    Response: explanation with top contributing factors
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        df = pd.DataFrame([data])
        
        missing_features = set(feature_columns) - set(df.columns)
        if missing_features:
            return jsonify({
                'error': f'Missing features: {list(missing_features)}',
                'required_features': feature_columns
            }), 400
        
        X = df[feature_columns]
        
        # Get prediction
        prediction = model.predict(X)[0]
        prediction_proba = model.predict_proba(X)[0]
        risk_level = reverse_label_mapping.get(prediction, 'Unknown')
        confidence = float(max(prediction_proba))
        
        # Get feature importances from the model
        feature_importances = model.feature_importances_
        
        # Calculate contribution of each feature
        # Using: importance * normalized_value as proxy for SHAP
        contributions = []
        
        for i, col in enumerate(feature_columns):
            value = float(X[col].values[0])
            importance = feature_importances[i]
            
            # Normalize value to 0-1 range for scoring
            # Higher values generally increase risk
            if col in ['cvss_base_score', 'cvss_combined']:
                normalized = value / 10.0  # 0-10 scale
            elif col in ['exploitability_score', 'impact_score']:
                normalized = value / 6.0  # 0-6 scale typically
            elif col in ['attack_ease_score']:
                normalized = value / 3.0  # 0-3 scale
            elif col in ['severity_score']:
                normalized = value / 4.0  # 0-4 scale
            elif col in ['public_exposure']:
                normalized = value  # 0 or 1
            elif col in ['age_factor']:
                normalized = value  # already 0-1
            else:
                normalized = value / 3.0  # encoded values typically 0-3
            
            # Contribution = importance * normalized_value * 10 (scale to readable)
            contribution = importance * normalized * 10
            
            # Determine direction (increase or decrease risk)
            if normalized > 0.5:
                direction = 'increased'
            else:
                direction = 'decreased'
                contribution = -abs(contribution) * 0.3  # smaller negative impact
            
            contributions.append({
                'feature': col,
                'feature_name': FEATURE_DESCRIPTIONS.get(col, col),
                'value': round(value, 2),
                'importance': round(importance, 4),
                'contribution': round(contribution, 2),
                'direction': direction
            })
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        # Get top 5 factors
        top_factors = contributions[:5]
        
        # Generate human-readable explanation
        explanation_text = f"This vulnerability is rated {risk_level} because:"
        
        return jsonify({
            'risk_level': risk_level,
            'confidence': round(confidence, 2),
            'explanation': explanation_text,
            'top_factors': top_factors,
            'all_factors': contributions
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/batch-predict', methods=['POST'])
def batch_predict():
    """Predict risk level for multiple vulnerabilities"""
    data = request.get_json()
    
    if not data or 'vulnerabilities' not in data:
        return jsonify({'error': 'No vulnerabilities provided'}), 400
    
    vulnerabilities = data['vulnerabilities']
    
    if not isinstance(vulnerabilities, list):
        return jsonify({'error': 'vulnerabilities must be a list'}), 400
    
    try:
        results = []
        
        for vuln in vulnerabilities:
            df = pd.DataFrame([vuln])
            X = df[feature_columns]
            
            prediction = model.predict(X)[0]
            prediction_proba = model.predict_proba(X)[0]
            
            risk_level = reverse_label_mapping.get(prediction, 'Unknown')
            confidence = float(max(prediction_proba))
            
            results.append({
                'risk_level': risk_level,
                'confidence': confidence
            })
        
        return jsonify({
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting ML Risk Scorer API with SHAP Explanations...")
    print("="*60)
    print(f"\n📍 API available at: http://localhost:5000")
    print(f"📖 Documentation: http://localhost:5000/")
    print(f"🔮 Explain endpoint: POST /explain")
    print(f"❤️  Health check: http://localhost:5000/health")
    print(f"\n⚡ Press CTRL+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)