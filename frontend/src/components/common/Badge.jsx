import React from 'react';
import { getSeverityColor } from '../../utils/helpers';

const Badge = ({ severity, className = '' }) => {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
        ${getSeverityColor(severity)}
        ${className}
      `}
    >
      {severity}
    </span>
  );
};

export default Badge;
