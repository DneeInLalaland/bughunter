import React from 'react';
import { CheckCircle, Loader, XCircle, AlertCircle } from 'lucide-react';

const ScanProgress = ({ scan }) => {
  const progress = scan.progress || 0;
  const statusMessage = scan.status_message || '';

  const getStatusIcon = () => {
    switch (scan.status) {
      case 'completed':
        return <CheckCircle className="h-12 w-12 text-green-500" />;
      case 'failed':
        return <XCircle className="h-12 w-12 text-red-500" />;
      case 'running':
        return <Loader className="h-12 w-12 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-12 w-12 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (scan.status) {
      case 'pending':
        return 'Scan queued...';
      case 'running':
        return 'Scanning in progress...';
      case 'completed':
        return 'Scan completed!';
      case 'failed':
        return 'Scan failed';
      default:
        return scan.status;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <div className="flex flex-col items-center text-center">
        {getStatusIcon()}
        
        <h3 className="mt-4 text-2xl font-semibold text-gray-900">
          {getStatusText()}
        </h3>
        
        <p className="mt-2 text-gray-600">
          Target: {scan.target_url}
        </p>

        {(scan.status === 'running' || scan.status === 'pending') && (
          <div className="mt-6 w-full max-w-md">
            <div className="bg-gray-200 rounded-full h-4 overflow-hidden">
              <div 
                className="bg-gray-800 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            
            <div className="flex justify-between mt-2">
              <span className="text-sm text-gray-600">
                {statusMessage || 'Processing...'}
              </span>
              <span className="text-sm font-bold text-gray-900">
                {progress}%
              </span>
            </div>
          </div>
        )}

        {scan.status === 'completed' && (
          <div className="mt-6 grid grid-cols-2 gap-4 w-full max-w-md">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Total Vulnerabilities</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {scan.total_vulnerabilities || 0}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Critical Issues</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {scan.critical_count || 0}
              </p>
            </div>
          </div>
        )}

        {scan.status === 'failed' && scan.error_message && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 w-full max-w-md">
            <p className="text-sm text-red-800">{scan.error_message}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanProgress;
