import React, { useState } from 'react';
import { Globe } from 'lucide-react';
import Button from '../common/Button';

const ScanForm = ({ onSubmit, loading }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (url) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }
    if (!validateUrl(url)) {
      setError('Please enter a valid URL (e.g., https://example.com)');
      return;
    }
    setError('');
    onSubmit(url);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
          Target URL
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Globe className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            disabled={loading}
            className={`
              block w-full pl-10 pr-3 py-3 border rounded-lg
              focus:ring-2 focus:ring-primary-500 focus:border-transparent
              ${error ? 'border-red-300' : 'border-gray-300'}
              ${loading ? 'bg-gray-100 cursor-not-allowed' : ''}
            `}
          />
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      <Button
        type="submit"
        loading={loading}
        disabled={loading}
        className="w-full"
        size="lg"
      >
        {loading ? 'Starting scan...' : 'Start Scan'}
      </Button>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> Only scan websites you own or have permission to test.
          Unauthorized scanning may be illegal.
        </p>
      </div>
    </form>
  );
};

export default ScanForm;
