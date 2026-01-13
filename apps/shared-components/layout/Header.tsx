import React from 'react'
import { Link } from 'react-router-dom'

interface HeaderProps {
  title?: string
}

export default function Header({ title = "Stock Arena" }: HeaderProps) {
  return (
    <header className="border-b border-gray-200 bg-white px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        </div>
        <nav className="flex items-center space-x-6">
          <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 transition-colors">
            Dashboard
          </Link>
          <Link to="/klines" className="text-gray-600 hover:text-gray-900 transition-colors">
            K Lines
          </Link>
          <Link to="/patterns" className="text-gray-600 hover:text-gray-900 transition-colors">
            Patterns
          </Link>
          <Link to="/ai" className="text-gray-600 hover:text-gray-900 transition-colors">
            AI Decision
          </Link>
          <Link to="/signals" className="text-gray-600 hover:text-gray-900 transition-colors">
            Signals
          </Link>
          <Link to="/ranking" className="text-gray-600 hover:text-gray-900 transition-colors">
            Ranking
          </Link>
          <Link to="/portfolio" className="text-gray-600 hover:text-gray-900 transition-colors">
            Portfolio
          </Link>
        </nav>
      </div>
    </header>
  )
}
