// Format date
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Format relative time (e.g., "2 hours ago")
export const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) {
    return 'เมื่อสักครู่';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} นาทีที่แล้ว`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} ชั่วโมงที่แล้ว`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} วันที่แล้ว`;
  }
};

// Get severity color
export const getSeverityColor = (severity) => {
  const colors = {
    Critical: 'text-danger-600 bg-danger-50 border-danger-200',
    High: 'text-orange-600 bg-orange-50 border-orange-200',
    Medium: 'text-warning-600 bg-warning-50 border-warning-200',
    Low: 'text-blue-600 bg-blue-50 border-blue-200',
  };
  return colors[severity] || 'text-gray-600 bg-gray-50 border-gray-200';
};

// Get status color
export const getStatusColor = (status) => {
  const colors = {
    pending: 'text-gray-600 bg-gray-100',
    running: 'text-blue-600 bg-blue-100',
    completed: 'text-success-600 bg-success-100',
    failed: 'text-danger-600 bg-danger-100',
  };
  return colors[status] || 'text-gray-600 bg-gray-100';
};

// Truncate text
export const truncateText = (text, maxLength) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
