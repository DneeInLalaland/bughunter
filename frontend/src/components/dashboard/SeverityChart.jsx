import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts';

const SeverityChart = ({ data }) => {
  const COLORS = {
    Critical: '#dc2626',
    High: '#f97316',
    Medium: '#f59e0b',
    Low: '#3b82f6',
  };

  const chartData = [
    { name: 'Critical', value: data.critical || 0 },
    { name: 'High', value: data.high || 0 },
    { name: 'Medium', value: data.medium || 0 },
    { name: 'Low', value: data.low || 0 },
  ].filter(item => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default SeverityChart;
