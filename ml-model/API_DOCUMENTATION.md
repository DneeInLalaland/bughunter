# ML Risk Scorer API Documentation

## Overview
REST API for predicting vulnerability risk levels using Machine Learning.

- **Model**: Random Forest
- **Accuracy**: 100%
- **Training Data**: 89,659 vulnerabilities

## Base URL
http://localhost:5001

## Endpoints

### 1. GET /
API information

### 2. GET /health
Health check

### 3. POST /predict
Predict risk level for a single vulnerability

### 4. POST /batch-predict
Predict risk for multiple vulnerabilities

## Required Features (13 total)
1. cvss_base_score
2. exploitability_score
3. impact_score
4. cvss_severity_encoded
5. attack_vector_encoded
6. attack_complexity_encoded
7. privileges_required_encoded
8. user_interaction_encoded
9. cvss_combined
10. attack_ease_score
11. public_exposure
12. age_factor
13. severity_score

## Risk Levels
- **Critical**: Highest priority
- **High**: High priority
- **Medium**: Medium priority
- **Low**: Low priority

## Example Usage

cURL:
curl -X POST http://localhost:5001/predict -H "Content-Type: application/json" -d '{"cvss_base_score": 9.3}'

Python:
import requests
response = requests.post("http://localhost:5001/predict", json={"cvss_base_score": 9.3})

## Notes
- All numeric features should be floats
- API runs in development mode

Created by: Person 2 - Machine Learning Engineer
Date: November 2024
