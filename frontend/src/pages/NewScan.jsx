import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScanForm from '../components/scan/ScanForm';
import ScanProgress from '../components/scan/ScanProgress';
import Button from '../components/common/Button';
import { scanAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Eye } from 'lucide-react';

const NewScan = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [scanData, setScanData] = useState(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    let interval;
    if (polling && scanData && scanData.id) {
      interval = setInterval(async () => {
        try {
          const updatedScan = await scanAPI.getScan(scanData.id);
          setScanData(updatedScan);
          
          if (updatedScan.status === 'completed' || updatedScan.status === 'failed') {
            setPolling(false);
          }
        } catch (error) {
          console.error('Error polling scan:', error);
        }
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [polling, scanData]);

  const handleSubmit = async (url) => {
    try {
      setLoading(true);
      const response = await scanAPI.createScan(url);
      
      setScanData({
        id: response.id,
        target_url: url,
        status: 'running',
        progress: 5,
        status_message: 'Initializing scan...'
      });
      
      setPolling(true);
      toast.success('Scan started successfully!');
    } catch (error) {
      console.error('Error creating scan:', error);
      toast.error('Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  const handleViewResults = () => {
    navigate(`/scans/${scanData.id}`);
  };

  const handleNewScan = () => {
    setScanData(null);
    setPolling(false);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">New Security Scan</h1>
        <p className="mt-2 text-gray-600">
          Enter a URL to scan for security vulnerabilities
        </p>
      </div>

      {!scanData ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <ScanForm onSubmit={handleSubmit} loading={loading} />
        </div>
      ) : (
        <div className="space-y-4">
          <ScanProgress scan={scanData} />

          {scanData.status === 'completed' && (
            <div className="flex gap-4">
              <Button onClick={handleViewResults} icon={Eye} className="flex-1" size="lg">
                View Results
              </Button>
              <Button onClick={handleNewScan} variant="outline" className="flex-1" size="lg">
                New Scan
              </Button>
            </div>
          )}

          {scanData.status === 'failed' && (
            <Button onClick={handleNewScan} variant="primary" className="w-full" size="lg">
              Try Again
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default NewScan;
