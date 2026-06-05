import React, { useState, useEffect } from 'react';
import { X, HelpCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import api from '../services/api';

const WhyModal = ({ isOpen, onClose, vulnerabilityId, vulnerabilityType, severity }) => {
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && vulnerabilityId) {
      fetchExplanation();
    }
  }, [isOpen, vulnerabilityId]);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/explain/${vulnerabilityId}`);
      setExplanation(response.data);
    } catch (err) {
      console.error('Failed to fetch explanation:', err);
      setError('Failed to load explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const getDirectionIcon = (direction) => {
    if (direction === 'increased') {
      return <TrendingUp className="w-4 h-4 text-red-500" />;
    } else if (direction === 'decreased') {
      return <TrendingDown className="w-4 h-4 text-green-500" />;
    }
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getContributionColor = (contribution) => {
    if (contribution > 1.5) return 'text-red-600 bg-red-50';
    if (contribution > 0.5) return 'text-orange-600 bg-orange-50';
    if (contribution > 0) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getSeverityColor = (sev) => {
    const colors = {
      'Critical': 'bg-red-100 text-red-800 border-red-200',
      'High': 'bg-orange-100 text-orange-800 border-orange-200',
      'Medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Low': 'bg-green-100 text-green-800 border-green-200',
    };
    return colors[sev] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg z-50 transform transition-all">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <HelpCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Why this risk level?
                </h3>
                <p className="text-sm text-gray-500">
                  AI-powered risk analysis
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-5">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-8">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-500">Analyzing vulnerability...</p>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-500">{error}</p>
                <button
                  onClick={fetchExplanation}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Try Again
                </button>
              </div>
            ) : explanation ? (
              <div className="space-y-5">
                {/* Vulnerability Info */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-500">Vulnerability</p>
                    <p className="font-medium text-gray-900">{explanation.vulnerability_type}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSeverityColor(explanation.severity)}`}>
                    {explanation.severity}
                  </span>
                </div>

                {/* Confidence */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">AI Confidence:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${(explanation.confidence || 0.8) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    {Math.round((explanation.confidence || 0.8) * 100)}%
                  </span>
                </div>

                {/* Explanation Text */}
                <p className="text-gray-700 font-medium">
                  {explanation.explanation || `This vulnerability is rated ${explanation.severity} because:`}
                </p>

                {/* Top Factors */}
                <div className="space-y-3">
                  <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                    Top Contributing Factors
                  </p>
                  
                  {explanation.top_factors && explanation.top_factors.map((factor, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {getDirectionIcon(factor.direction)}
                        <div>
                          <p className="font-medium text-gray-900">
                            {factor.feature_name}
                          </p>
                          <p className="text-sm text-gray-500">
                            Value: {typeof factor.value === 'number' ? factor.value.toFixed(1) : factor.value}
                          </p>
                        </div>
                      </div>
                      <div className={`px-3 py-1 rounded-lg text-sm font-semibold ${getContributionColor(factor.contribution)}`}>
                        {factor.contribution > 0 ? '+' : ''}{factor.contribution?.toFixed(1) || '0.0'}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Legend */}
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-400 text-center">
                    Positive values increase risk • Negative values decrease risk
                  </p>
                </div>
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="flex justify-end p-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
            <button
              onClick={onClose}
              className="px-5 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhyModal;