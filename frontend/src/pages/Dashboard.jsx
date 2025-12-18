import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [studyPlan, setStudyPlan] = useState(null)
  const [todayTasks, setTodayTasks] = useState([])
  const [error, setError] = useState(null)
  
  // For testing - use the user_id from create_test_user.py (typically 1)
  const TEST_USER_ID = 1

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch latest study plan
      try {
        const planResponse = await axios.get(`/api/v1/plans/user/${TEST_USER_ID}/latest`)
        setStudyPlan(planResponse.data)
        
        // Calculate today's tasks
        if (planResponse.data.weeks_data) {
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          
          const allTasks = []
          planResponse.data.weeks_data.forEach(week => {
            week.days?.forEach(day => {
              if (day.tasks) {
                day.tasks.forEach(task => {
                  if (task.task_date) {
                    const taskDate = new Date(task.task_date)
                    taskDate.setHours(0, 0, 0, 0)
                    if (taskDate.getTime() === today.getTime()) {
                      allTasks.push({ ...task, day: day })
                    }
                  }
                })
              }
            })
          })
          
          setTodayTasks(allTasks)
        }
      } catch (planError) {
        if (planError.response?.status !== 404) {
          console.error('Error fetching study plan:', planError)
        }
        // 404 is OK - no plan exists yet
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="px-4 py-8">
        <div className="text-center">Loading dashboard...</div>
      </div>
    )
  }

  // Calculate stats
  const weeksRemaining = studyPlan 
    ? Math.max(0, studyPlan.weeks - (studyPlan.weeks_data?.length || 0))
    : null
  
  const completedToday = todayTasks.filter(t => t.status === 'completed').length
  const totalToday = todayTasks.length

  return (
    <div className="px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
        
        {!studyPlan && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <p className="text-yellow-800 mb-4">
              No study plan found. Generate one by uploading your resume and job description!
            </p>
            <Link
              to="/upload"
              className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Go to Upload Page
            </Link>
          </div>
        )}

        {studyPlan && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold text-gray-700 mb-2">Study Plan</h2>
                <p className="text-3xl font-bold text-primary-600">
                  {studyPlan.weeks || 0}
                </p>
                <p className="text-sm text-gray-500 mt-1">Total weeks</p>
                {studyPlan.interview_date && (
                  <p className="text-xs text-gray-400 mt-1">
                    Interview: {new Date(studyPlan.interview_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold text-gray-700 mb-2">Daily Tasks</h2>
                <p className="text-3xl font-bold text-primary-600">
                  {completedToday}/{totalToday}
                </p>
                <p className="text-sm text-gray-500 mt-1">Completed today</p>
                {totalToday === 0 && (
                  <p className="text-xs text-gray-400 mt-1">No tasks scheduled for today</p>
                )}
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold text-gray-700 mb-2">Progress</h2>
                <p className="text-3xl font-bold text-primary-600">
                  {studyPlan.completion_percentage?.toFixed(0) || 0}%
                </p>
                <p className="text-sm text-gray-500 mt-1">Plan completion</p>
                <p className="text-xs text-gray-400 mt-1">
                  {studyPlan.total_estimated_hours?.toFixed(1) || 0}h total
                </p>
              </div>
            </div>

            {/* Today's Tasks */}
            {todayTasks.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Today's Tasks</h2>
                <div className="space-y-3">
                  {todayTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            task.task_type === 'learn' ? 'bg-blue-100 text-blue-800' :
                            task.task_type === 'practice' ? 'bg-green-100 text-green-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {task.task_type}
                          </span>
                          <div>
                            <p className="font-semibold text-gray-900">{task.title}</p>
                            {task.description && (
                              <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                            )}
                            {task.skill_names && task.skill_names.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {task.skill_names.map((skill, idx) => (
                                  <span key={idx} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-gray-700">{task.estimated_minutes}min</p>
                          <span className={`text-xs px-2 py-1 rounded ${
                            task.status === 'completed' ? 'bg-green-100 text-green-800' :
                            task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {task.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Study Plan Overview */}
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Study Plan Overview</h2>
              
              {studyPlan.focus_areas && studyPlan.focus_areas.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Focus Areas</h3>
                  <div className="flex flex-wrap gap-2">
                    {studyPlan.focus_areas.map((area, idx) => (
                      <span key={idx} className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {studyPlan.weeks_data && studyPlan.weeks_data.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Weekly Progress</h3>
                  <div className="space-y-2">
                    {studyPlan.weeks_data.map((week) => {
                      const weekTasks = week.days?.flatMap(d => d.tasks || []) || []
                      const completedWeekTasks = weekTasks.filter(t => t.status === 'completed').length
                      const totalWeekTasks = weekTasks.length
                      const weekProgress = totalWeekTasks > 0 ? (completedWeekTasks / totalWeekTasks) * 100 : 0
                      
                      return (
                        <div key={week.id} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex justify-between items-center mb-2">
                            <div>
                              <p className="font-semibold text-gray-900">
                                Week {week.week_number}: {week.theme}
                              </p>
                              <p className="text-xs text-gray-600 mt-1">
                                {week.estimated_hours}h • {completedWeekTasks}/{totalWeekTasks} tasks
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-gray-700">{weekProgress.toFixed(0)}%</p>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full transition-all"
                              style={{ width: `${weekProgress}%` }}
                            ></div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Recent Activity */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
              <div className="space-y-2 text-sm text-gray-600">
                {studyPlan.created_at && (
                  <p>✓ Study plan created on {new Date(studyPlan.created_at).toLocaleDateString()}</p>
                )}
                {studyPlan.updated_at && studyPlan.updated_at !== studyPlan.created_at && (
                  <p>✓ Plan last updated on {new Date(studyPlan.updated_at).toLocaleDateString()}</p>
                )}
                {completedToday > 0 && (
                  <p className="text-green-600 font-semibold">
                    ✓ Completed {completedToday} task{completedToday > 1 ? 's' : ''} today
                  </p>
                )}
                {totalToday === 0 && (
                  <p className="text-gray-500">No tasks scheduled for today</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard




