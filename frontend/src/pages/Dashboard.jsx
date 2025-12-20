import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function Dashboard() {
  // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
  const [loading, setLoading] = useState(true)
  const [studyPlan, setStudyPlan] = useState(null)
  const [todayTasks, setTodayTasks] = useState([])
  const [error, setError] = useState(null)
  const [expandedTasks, setExpandedTasks] = useState(new Set())
  const [expandedWeek, setExpandedWeek] = useState(null)
  const [masteryStats, setMasteryStats] = useState(null) // Phase 9
  
  // For testing - use the user_id from create_test_user.py (typically 1)
  const TEST_USER_ID = 1

  // OPTIMIZATION: Memoize expensive calculations - MUST be before any conditional returns
  const weeksRemaining = useMemo(() => {
    return studyPlan 
      ? Math.max(0, studyPlan.weeks - (studyPlan.weeks_data?.length || 0))
      : null
  }, [studyPlan])
  
  const completedToday = useMemo(() => {
    return todayTasks.filter(t => t.status === 'completed').length
  }, [todayTasks])

  useEffect(() => {
    fetchDashboardData()
    fetchMasteryStats() // Phase 9
  }, [])

  const fetchMasteryStats = async () => {
    try {
      const response = await axios.get(`/api/v1/mastery/user/${TEST_USER_ID}/stats`)
      setMasteryStats(response.data)
    } catch (err) {
      // Mastery stats are optional, so don't show error
      console.warn('Could not fetch mastery stats:', err)
    }
  }

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch latest study plan
      try {
        const planResponse = await axios.get(`/api/v1/plans/user/${TEST_USER_ID}/latest`)
        setStudyPlan(planResponse.data)
        
        // OPTIMIZATION: Calculate today's tasks more efficiently
        if (planResponse.data.weeks_data) {
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          const todayTime = today.getTime()
          
          // Flatten and filter in a single pass
          try {
            const allTasks = planResponse.data.weeks_data
              .flatMap(week => week.days || [])
              .flatMap(day => (day.tasks || []).map(task => ({ ...task, day })))
              .filter(task => {
                if (!task.task_date) return false
                try {
                  const taskDate = new Date(task.task_date)
                  taskDate.setHours(0, 0, 0, 0)
                  return taskDate.getTime() === todayTime
                } catch (e) {
                  console.warn('Invalid task_date:', task.task_date, e)
                  return false
                }
              })
            
            setTodayTasks(allTasks)
          } catch (taskError) {
            console.error('Error processing tasks:', taskError)
            setTodayTasks([])
          }
        }
      } catch (planError) {
        if (planError.response?.status !== 404) {
          console.error('Error fetching study plan:', planError)
          setError(planError.response?.data?.detail || planError.message || 'Failed to load study plan')
        } else {
          // 404 is OK - no plan exists yet
          setStudyPlan(null)
          setTodayTasks([])
        }
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Helper functions - can be after hooks but before conditional returns
  const totalToday = todayTasks.length

  // Conditional returns - AFTER all hooks
  if (loading) {
    return (
      <div className="px-4 py-8">
        <div className="text-center">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Error: {error}</p>
          <button
            onClick={fetchDashboardData}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const toggleTaskExpansion = (taskId) => {
    const newExpanded = new Set(expandedTasks)
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId)
    } else {
      newExpanded.add(taskId)
    }
    setExpandedTasks(newExpanded)
  }

  const toggleWeekExpansion = (weekId) => {
    setExpandedWeek(expandedWeek === weekId ? null : weekId)
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <Link
            to="/coach"
            className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
          >
            View Daily Coach
          </Link>
        </div>
        
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

            {/* Mastery Stats Section - Phase 9 */}
            <div className="bg-white p-6 rounded-lg shadow mb-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">📊 Skill Mastery Overview</h2>
                <button
                  onClick={fetchMasteryStats}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  title="Refresh mastery stats"
                >
                  🔄 Refresh
                </button>
              </div>
              {masteryStats ? (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Average Mastery</p>
                      <p className="text-2xl font-bold text-primary-600">
                        {(masteryStats.average_mastery * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Skills</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {masteryStats.total_skills}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Practice</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {masteryStats.total_practice_count}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">This Week</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {masteryStats.recent_practice_count}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-blue-50 p-3 rounded">
                      <p className="text-xs text-blue-700 font-semibold">Beginner</p>
                      <p className="text-lg font-bold text-blue-900">
                        {masteryStats.skills_by_level?.beginner || 0}
                      </p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded">
                      <p className="text-xs text-yellow-700 font-semibold">Intermediate</p>
                      <p className="text-lg font-bold text-yellow-900">
                        {masteryStats.skills_by_level?.intermediate || 0}
                      </p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded">
                      <p className="text-xs text-orange-700 font-semibold">Advanced</p>
                      <p className="text-lg font-bold text-orange-900">
                        {masteryStats.skills_by_level?.advanced || 0}
                      </p>
                    </div>
                    <div className="bg-green-50 p-3 rounded">
                      <p className="text-xs text-green-700 font-semibold">Expert</p>
                      <p className="text-lg font-bold text-green-900">
                        {masteryStats.skills_by_level?.expert || 0}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-green-600 font-semibold">↑</span>
                      <span className="text-gray-700">
                        {masteryStats.improving_skills} Improving
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 font-semibold">→</span>
                      <span className="text-gray-700">
                        {masteryStats.stable_skills} Stable
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-red-600 font-semibold">↓</span>
                      <span className="text-gray-700">
                        {masteryStats.declining_skills} Declining
                      </span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No mastery data yet. Start practicing to see your progress!</p>
                  <p className="text-sm mt-2">Submit practice attempts to track your skill mastery.</p>
                </div>
              )}
            </div>

            {/* Today's Tasks */}
            {todayTasks.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Today's Tasks</h2>
                <div className="space-y-3">
                  {todayTasks.map((task) => {
                    const isExpanded = expandedTasks.has(task.id)
                    const content = task.content || {}
                    const studyMaterials = content.study_materials || []
                    const resources = content.resources || []
                    const keyConcepts = content.key_concepts || []
                    const practiceExercises = content.practice_exercises || []
                    
                    return (
                      <div key={task.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => toggleTaskExpansion(task.id)}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 flex-1">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              task.task_type === 'learn' ? 'bg-blue-100 text-blue-800' :
                              task.task_type === 'practice' ? 'bg-green-100 text-green-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {task.task_type}
                            </span>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-semibold text-gray-900">{task.title}</p>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleTaskExpansion(task.id)
                                  }}
                                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                                >
                                  {isExpanded ? '▼ Hide Materials' : '▶ View Study Materials'}
                                </button>
                              </div>
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
                          <div className="text-right ml-4">
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
                        
                        {/* Expanded Study Materials */}
                        {isExpanded && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200" onClick={(e) => e.stopPropagation()}>
                            {/* Study Materials */}
                            {studyMaterials.length > 0 && (
                              <div className="mb-4">
                                <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                                  <span className="mr-2">📚</span> What to Study
                                </h4>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                  {studyMaterials.map((material, idx) => (
                                    <li key={idx}>{material}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Key Concepts */}
                            {keyConcepts.length > 0 && (
                              <div className="mb-4">
                                <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                                  <span className="mr-2">💡</span> Key Concepts
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                  {keyConcepts.map((concept, idx) => (
                                    <span key={idx} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                      {concept}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Resources/Links */}
                            {resources.length > 0 && (
                              <div className="mb-4">
                                <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                                  <span className="mr-2">🔗</span> Resources & Links
                                </h4>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                  {resources.map((resource, idx) => (
                                    <li key={idx}>
                                      <a href={resource} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                                        {resource}
                                      </a>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Practice Exercises (for practice tasks) */}
                            {practiceExercises.length > 0 && task.task_type === 'practice' && (
                              <div className="mb-4">
                                <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                                  <span className="mr-2">📝</span> Practice Exercises
                                </h4>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                                  {practiceExercises.map((exercise, idx) => (
                                    <li key={idx}>{exercise}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Message if no additional content */}
                            {studyMaterials.length === 0 && resources.length === 0 && keyConcepts.length === 0 && practiceExercises.length === 0 && (
                              <p className="text-sm text-gray-500 italic">No additional study materials provided for this task.</p>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
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
                      // OPTIMIZATION: Calculate week stats efficiently
                      const weekTasks = week.days?.flatMap(d => d.tasks || []) || []
                      const completedWeekTasks = weekTasks.filter(t => t.status === 'completed').length
                      const totalWeekTasks = weekTasks.length
                      const weekProgress = totalWeekTasks > 0 ? (completedWeekTasks / totalWeekTasks) * 100 : 0
                      const isWeekExpanded = expandedWeek === week.id
                      
                      return (
                        <div key={week.id} className="border border-gray-200 rounded-lg p-3">
                          <div 
                            className="flex justify-between items-center mb-2 cursor-pointer"
                            onClick={() => toggleWeekExpansion(week.id)}
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-semibold text-gray-900">
                                  Week {week.week_number}: {week.theme}
                                </p>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleWeekExpansion(week.id)
                                  }}
                                  className="text-primary-600 hover:text-primary-700 text-xs font-medium"
                                >
                                  {isWeekExpanded ? '▼ Hide Tasks' : '▶ View Tasks'}
                                </button>
                              </div>
                              <p className="text-xs text-gray-600 mt-1">
                                {week.estimated_hours}h • {completedWeekTasks}/{totalWeekTasks} tasks
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-gray-700">{weekProgress.toFixed(0)}%</p>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full transition-all"
                              style={{ width: `${weekProgress}%` }}
                            ></div>
                          </div>
                          
                          {/* Expanded Week Tasks */}
                          {isWeekExpanded && (
                            <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                              {week.days?.map((day) => (
                                day.tasks?.map((task) => {
                                  const isTaskExpanded = expandedTasks.has(task.id)
                                  const content = task.content || {}
                                  const studyMaterials = content.study_materials || []
                                  const resources = content.resources || []
                                  const keyConcepts = content.key_concepts || []
                                  const practiceExercises = content.practice_exercises || []
                                  
                                  return (
                                    <div 
                                      key={task.id} 
                                      className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:shadow-sm transition-shadow cursor-pointer"
                                      onClick={() => toggleTaskExpansion(task.id)}
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 flex-1">
                                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                            task.task_type === 'learn' ? 'bg-blue-100 text-blue-800' :
                                            task.task_type === 'practice' ? 'bg-green-100 text-green-800' :
                                            'bg-yellow-100 text-yellow-800'
                                          }`}>
                                            {task.task_type}
                                          </span>
                                          <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                              <p className="font-medium text-gray-900 text-sm">{task.title}</p>
                                              <button
                                                onClick={(e) => {
                                                  e.stopPropagation()
                                                  toggleTaskExpansion(task.id)
                                                }}
                                                className="text-primary-600 hover:text-primary-700 text-xs font-medium"
                                              >
                                                {isTaskExpanded ? '▼' : '▶'}
                                              </button>
                                            </div>
                                            {task.skill_names && task.skill_names.length > 0 && (
                                              <div className="flex flex-wrap gap-1 mt-1">
                                                {task.skill_names.map((skill, idx) => (
                                                  <span key={idx} className="bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded text-xs">
                                                    {skill}
                                                  </span>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                        <div className="text-right ml-2">
                                          <p className="text-xs font-semibold text-gray-700">{task.estimated_minutes}min</p>
                                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                                            task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                            task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-gray-100 text-gray-800'
                                          }`}>
                                            {task.status}
                                          </span>
                                        </div>
                                      </div>
                                      
                                      {/* Expanded Study Materials */}
                                      {isTaskExpanded && (
                                        <div className="mt-3 p-3 bg-white rounded border border-gray-200" onClick={(e) => e.stopPropagation()}>
                                          {studyMaterials.length > 0 && (
                                            <div className="mb-3">
                                              <h5 className="font-semibold text-gray-900 mb-1 text-xs flex items-center">
                                                <span className="mr-1">📚</span> Study Materials
                                              </h5>
                                              <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-700 ml-2">
                                                {studyMaterials.map((material, idx) => (
                                                  <li key={idx}>{material}</li>
                                                ))}
                                              </ul>
                                            </div>
                                          )}
                                          
                                          {keyConcepts.length > 0 && (
                                            <div className="mb-3">
                                              <h5 className="font-semibold text-gray-900 mb-1 text-xs flex items-center">
                                                <span className="mr-1">💡</span> Key Concepts
                                              </h5>
                                              <div className="flex flex-wrap gap-1 ml-2">
                                                {keyConcepts.map((concept, idx) => (
                                                  <span key={idx} className="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded text-xs">
                                                    {concept}
                                                  </span>
                                                ))}
                                              </div>
                                            </div>
                                          )}
                                          
                                          {resources.length > 0 && (
                                            <div className="mb-3">
                                              <h5 className="font-semibold text-gray-900 mb-1 text-xs flex items-center">
                                                <span className="mr-1">🔗</span> Resources
                                              </h5>
                                              <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-700 ml-2">
                                                {resources.map((resource, idx) => (
                                                  <li key={idx}>
                                                    <a href={resource} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                                                      {resource}
                                                    </a>
                                                  </li>
                                                ))}
                                              </ul>
                                            </div>
                                          )}
                                          
                                          {practiceExercises.length > 0 && task.task_type === 'practice' && (
                                            <div>
                                              <h5 className="font-semibold text-gray-900 mb-1 text-xs flex items-center">
                                                <span className="mr-1">📝</span> Practice Exercises
                                              </h5>
                                              <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-700 ml-2">
                                                {practiceExercises.map((exercise, idx) => (
                                                  <li key={idx}>{exercise}</li>
                                                ))}
                                              </ul>
                                            </div>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  )
                                })
                              ))}
                            </div>
                          )}
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




