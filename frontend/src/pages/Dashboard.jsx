import { useState, useEffect } from 'react'
import axios from 'axios'

function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    // TODO: Implement actual API call
    // fetchDashboardData()
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="px-4 py-8">
        <div className="text-center">Loading...</div>
      </div>
    )
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Study Plan</h2>
            <p className="text-3xl font-bold text-primary-600">-</p>
            <p className="text-sm text-gray-500 mt-1">Weeks remaining</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Daily Tasks</h2>
            <p className="text-3xl font-bold text-primary-600">-</p>
            <p className="text-sm text-gray-500 mt-1">Completed today</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Mastery</h2>
            <p className="text-3xl font-bold text-primary-600">-</p>
            <p className="text-sm text-gray-500 mt-1">Average score</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <p className="text-gray-600">
            Dashboard functionality will be implemented in Phase 2.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard



