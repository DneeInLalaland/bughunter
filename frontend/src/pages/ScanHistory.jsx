import React, { useState, useEffect } from 'react';
import RecentScans from '../components/dashboard/RecentScans';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { scanAPI } from '../services/api';
import toast from 'react-hot-toast';

const ScanHistory = () => {
  const [loading, setLoading] = useState(true);
  const [scans, setScans] = useState([]);

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const scansData = await scanAPI.listScans(0, 100);
      setScans(scansData);
    } catch (error) {
      console.error('Error fetching scans:', error);
      toast.error('Failed to load scan history');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading scan history..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Scan History</h1>
        <p className="mt-1 text-gray-600">View all your previous scans</p>
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <RecentScans scans={scans} />
      </div>
    </div>
  );
};

export default ScanHistory;
