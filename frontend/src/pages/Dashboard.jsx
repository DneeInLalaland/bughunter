import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ScanSearch, AlertTriangle, ShieldCheck, Bug, Trash2 } from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import SeverityChart from '../components/dashboard/SeverityChart';
import VulnerabilityTypeChart from '../components/dashboard/VulnerabilityTypeChart';
import RecentScans from '../components/dashboard/RecentScans';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';
import { scanAPI } from '../services/api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [scans, setScans] = useState([]);
  const [allVulnerabilities, setAllVulnerabilities] = useState([]);
  const [stats, setStats] = useState({
    totalScans: 0,
    totalVulnerabilities: 0,
    criticalCount: 0,
    fixedCount: 0,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const scansData = await scanAPI.listScans(0, 10);
      setScans(scansData);

      // Collect all vulnerabilities from all scans
      let vulns = [];
      for (const scan of scansData) {
        if (scan.vulnerabilities && scan.vulnerabilities.length > 0) {
          vulns = [...vulns, ...scan.vulnerabilities];
        } else if (scan.id) {
          // Fetch vulnerabilities for this scan if not included
          try {
            const scanDetail = await scanAPI.getScan(scan.id);
            if (scanDetail.vulnerabilities) {
              vulns = [...vulns, ...scanDetail.vulnerabilities];
            }
          } catch (e) {
            console.log('Could not fetch scan details:', e);
          }
        }
      }
      setAllVulnerabilities(vulns);

      const totalScans = scansData.length;
      const totalVulnerabilities = scansData.reduce(
        (sum, scan) => sum + (scan.total_vulnerabilities || 0),
        0
      );
      const criticalCount = scansData.reduce(
        (sum, scan) => sum + (scan.critical_count || 0),
        0
      );

      setStats({
        totalScans,
        totalVulnerabilities,
        criticalCount,
        fixedCount: 0,
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ ฟังก์ชัน Reset Dashboard
  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset all scan data? This cannot be undone!')) {
      return;
    }

    try {
      setResetting(true);
      await scanAPI.resetAllData();
      toast.success('Dashboard reset successfully!');
      
      // รีเซ็ต state
      setScans([]);
      setAllVulnerabilities([]);
      setStats({
        totalScans: 0,
        totalVulnerabilities: 0,
        criticalCount: 0,
        fixedCount: 0,
      });
    } catch (error) {
      console.error('Error resetting dashboard:', error);
      toast.error('Failed to reset dashboard');
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  const severityData = scans.reduce(
    (acc, scan) => {
      acc.critical += scan.critical_count || 0;
      acc.high += scan.high_count || 0;
      acc.medium += scan.medium_count || 0;
      acc.low += scan.low_count || 0;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 }
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-gray-600">Overview of your security scans</p>
        </div>
        <div className="flex gap-3">
          {/* ✅ ปุ่ม Reset */}
          <Button 
            icon={Trash2} 
            size="lg" 
            variant="danger"
            onClick={handleReset}
            disabled={resetting}
          >
            {resetting ? 'Resetting...' : 'Reset'}
          </Button>
          <Link to="/scan/new">
            <Button icon={ScanSearch} size="lg">
              New Scan
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Scans" value={stats.totalScans} icon={ScanSearch} color="blue" />
        <StatCard title="Vulnerabilities Found" value={stats.totalVulnerabilities} icon={Bug} color="orange" />
        <StatCard title="Critical Issues" value={stats.criticalCount} icon={AlertTriangle} color="red" />
        <StatCard title="Fixed Issues" value={stats.fixedCount} icon={ShieldCheck} color="green" />
      </div>

      {/* Charts Row 1: Pie Chart & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Vulnerability by Severity</h2>
          <SeverityChart data={severityData} />
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Stats</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Critical</span>
              <span className="text-2xl font-bold text-red-600">{severityData.critical}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">High</span>
              <span className="text-2xl font-bold text-orange-600">{severityData.high}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Medium</span>
              <span className="text-2xl font-bold text-yellow-600">{severityData.medium}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Low</span>
              <span className="text-2xl font-bold text-blue-600">{severityData.low}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2: Bar Chart - Vulnerability by Type */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Vulnerabilities by Type</h2>
        <VulnerabilityTypeChart vulnerabilities={allVulnerabilities} />
      </div>

      {/* Recent Scans Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Recent Scans</h2>
        </div>
        <RecentScans scans={scans.slice(0, 5)} />
      </div>
    </div>
  );
};

export default Dashboard;