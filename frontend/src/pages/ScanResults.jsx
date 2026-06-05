import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  Filter,
  AlertTriangle,
  TrendingUp,
  Eye,
  RefreshCw,
} from 'lucide-react';
import VulnerabilityTable from '../components/vulnerabilities/VulnerabilityTable';
import NetworkGraph from '../components/vulnerabilities/NetworkGraph';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import { scanAPI } from '../services/api';
import toast from 'react-hot-toast';

const ScanResults = () => {
  const { scanId } = useParams();
  const [loading, setLoading] = useState(true);
  const [scan, setScan] = useState(null);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [filteredVulnerabilities, setFilteredVulnerabilities] = useState([]);
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [showGraph, setShowGraph] = useState(false);

  useEffect(() => {
    fetchScanResults();
  }, [scanId]);

  useEffect(() => {
    filterVulnerabilities();
  }, [selectedSeverity, vulnerabilities]);

  const fetchScanResults = async () => {
    try {
      setLoading(true);
      const scanData = await scanAPI.getScan(scanId);
      setScan(scanData);
      
      // Extract vulnerabilities from scan data
      const vulns = scanData.vulnerabilities || [];
      setVulnerabilities(vulns);
    } catch (error) {
      console.error('Error fetching scan results:', error);
      toast.error('Failed to load scan results');
    } finally {
      setLoading(false);
    }
  };

  const filterVulnerabilities = () => {
    if (selectedSeverity === 'all') {
      setFilteredVulnerabilities(vulnerabilities);
    } else {
      setFilteredVulnerabilities(
        vulnerabilities.filter((v) => v.severity === selectedSeverity)
      );
    }
  };

  const handleDownloadReport = async () => {
    try {
      setDownloadingReport(true);
      toast.loading('Generating PDF report...', { id: 'download' });
      
      // Direct download from API
      const API_BASE = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/reports/${scanId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `vulnerability_report_scan_${scanId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Report downloaded successfully!', { id: 'download' });
    } catch (error) {
      console.error('Error downloading report:', error);
      toast.error('Failed to download report', { id: 'download' });
    } finally {
      setDownloadingReport(false);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading results..." />;
  }

  if (!scan) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">Scan not found</p>
      </div>
    );
  }

  // Calculate severity counts from vulnerabilities
  const criticalCount = vulnerabilities.filter(v => v.severity === 'Critical').length;
  const highCount = vulnerabilities.filter(v => v.severity === 'High').length;
  const mediumCount = vulnerabilities.filter(v => v.severity === 'Medium').length;
  const lowCount = vulnerabilities.filter(v => v.severity === 'Low').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center space-x-4">
          <Link to="/scans">
            <button className="inline-flex items-center px-4 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Scan Results</h1>
            <p className="mt-1 text-gray-600 truncate max-w-md">{scan.target_url}</p>
          </div>
        </div>
        
        {/* ✅ FIXED: Download Button with visible text (blue background, white text) */}
        <button 
          onClick={handleDownloadReport}
          disabled={downloadingReport}
          className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md"
        >
          {downloadingReport ? (
            <>
              <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-5 w-5 mr-2" />
              Download Report
            </>
          )}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <p className="text-sm text-gray-600">Total Vulnerabilities</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {vulnerabilities.length}
          </p>
        </div>
        <div className="bg-red-50 rounded-lg shadow-sm p-6 border border-red-200">
          <p className="text-sm text-red-600">Critical</p>
          <p className="text-3xl font-bold text-red-600 mt-2">
            {criticalCount}
          </p>
        </div>
        <div className="bg-orange-50 rounded-lg shadow-sm p-6 border border-orange-200">
          <p className="text-sm text-orange-600">High</p>
          <p className="text-3xl font-bold text-orange-600 mt-2">
            {highCount}
          </p>
        </div>
        <div className="bg-yellow-50 rounded-lg shadow-sm p-6 border border-yellow-200">
          <p className="text-sm text-yellow-600">Medium</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">
            {mediumCount}
          </p>
        </div>
        <div className="bg-blue-50 rounded-lg shadow-sm p-6 border border-blue-200">
          <p className="text-sm text-blue-600">Low</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {lowCount}
          </p>
        </div>
      </div>

      {/* Filters & Graph Toggle */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center space-x-4">
          <Filter className="h-5 w-5 text-gray-600" />
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 px-3 py-2"
          >
            <option value="all">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <span className="text-sm text-gray-600">
            Showing {filteredVulnerabilities.length} vulnerabilities
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowGraph(!showGraph)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            {showGraph ? 'Hide' : 'Show'} Network Graph
          </button>
          <button
            onClick={fetchScanResults}
            className="inline-flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Network Graph */}
      {showGraph && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Attack Surface Map
          </h2>
          <NetworkGraph vulnerabilities={filteredVulnerabilities} />
        </div>
      )}

      {/* Vulnerabilities Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Vulnerabilities Found
          </h2>
        </div>
        <VulnerabilityTable vulnerabilities={filteredVulnerabilities} />
      </div>
    </div>
  );
};

export default ScanResults;