import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from '@shared/layout/Header'

function Dashboard() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Total Stocks</h3>
          <p className="text-3xl font-bold text-blue-600">0</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Active Signals</h3>
          <p className="text-3xl font-bold text-green-600">0</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">AI Decisions</h3>
          <p className="text-3xl font-bold text-purple-600">0</p>
        </div>
      </div>
    </div>
  )
}

function KLiness() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">K Lines</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">K线图表功能开发中...</p>
      </div>
    </div>
  )
}

function Patterns() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Patterns</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">形态识别功能开发中...</p>
      </div>
    </div>
  )
}

function AIDecision() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">AI Decision</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">AI决策功能开发中...</p>
      </div>
    </div>
  )
}

function Signals() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Signals</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">信号池功能开发中...</p>
      </div>
    </div>
  )
}

function Ranking() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Ranking</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">股票排名功能开发中...</p>
      </div>
    </div>
  )
}

function Portfolio() {
  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Portfolio</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">投资组合功能开发中...</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/klines" element={<KLiness />} />
            <Route path="/patterns" element={<Patterns />} />
            <Route path="/ai" element={<AIDecision />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/ranking" element={<Ranking />} />
            <Route path="/portfolio" element={<Portfolio />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}
