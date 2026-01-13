import React from 'react'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <p className="text-gray-600 text-sm">
            &copy; 2025 Stock Arena. All rights reserved.
          </p>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <a href="/docs" className="hover:text-gray-900 transition-colors">
              Documentation
            </a>
            <a href="/support" className="hover:text-gray-900 transition-colors">
              Support
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
