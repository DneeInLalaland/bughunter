import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Menu } from 'lucide-react';

const Navbar = ({ onMenuClick }) => {
  return (
    <nav className="bg-white border-b border-gray-200 fixed w-full z-30 top-0">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">

          {/* Left Section */}
          <div className="flex items-center">

            {/* Mobile menu button */}
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              <Menu className="h-6 w-6" />
            </button>

            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2 ml-2 lg:ml-0">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">BugHunter</span>
            </Link>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:block">
              <span className="text-sm text-gray-600">
                AI-Powered Vulnerability Scanner
              </span>
            </div>
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;
