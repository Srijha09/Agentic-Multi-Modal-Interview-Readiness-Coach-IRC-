import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function DailyCoach() {
  const [loading, setLoading] = useState(true)
  const [briefing, setBriefing] = useState(null)
  const [error, setError] = useState(null)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [rescheduleModal, setRescheduleModal] = useState({ open: false, task: null, newDate: '' })
  const [carryOverModal, setCarryOverModal] = useState({ open: false, fromDate: '', toDate: '' })
  const [enriching, setEnriching] = useState(false)
  const [pomodoro, setPomodoro] = useState({
    isRunning: false,
    isBreak: false,
    timeLeft: 25 * 60, // 25 minutes in seconds
    completedPomodoros: 0,
    currentTaskId: null
  })
  
  const TEST_USER_ID = 1

  useEffect(() => {
    fetchBriefing()
  }, [selectedDate])

  // Pomodoro timer effect
  useEffect(() => {
    let interval = null
    if (pomodoro.isRunning && pomodoro.timeLeft > 0) {
      interval = setInterval(() => {
        setPomodoro(prev => {
          if (prev.timeLeft <= 1) {
            // Timer finished
            const isBreak = !prev.isBreak
            const nextTime = isBreak 
              ? (prev.completedPomodoros % 4 === 3 ? 15 * 60 : 5 * 60) // Long break after 4 pomodoros
              : 25 * 60
            const nextCompleted = isBreak ? prev.completedPomodoros : prev.completedPomodoros + 1
            
            // Show browser notification if permission granted
            if ('Notification' in window && Notification.permission === 'granted') {
              new Notification(
                isBreak ? '🍅 Break Time!' : '⏱️ Pomodoro Complete!',
                {
                  body: isBreak 
                    ? `Take a ${prev.completedPomodoros % 4 === 3 ? '15' : '5'} minute break!`
                    : 'Great work! Time for a break.',
                  icon: '🍅'
                }
              )
            }
            
            return {
              ...prev,
              isBreak: isBreak,
              timeLeft: nextTime,
              completedPomodoros: nextCompleted,
              isRunning: false // Auto-pause when timer ends
            }
          }
          return { ...prev, timeLeft: prev.timeLeft - 1 }
        })
      }, 1000)
    } else if (pomodoro.timeLeft === 0) {
      clearInterval(interval)
    }
    return () => clearInterval(interval)
  }, [pomodoro.isRunning, pomodoro.timeLeft, pomodoro.isBreak])

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  const fetchBriefing = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get('/api/v1/coach/briefing', {
        params: {
          user_id: TEST_USER_ID,
          target_date: selectedDate
        }
      })
      setBriefing(response.data)
    } catch (err) {
      console.error('Error fetching briefing:', err)
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const completeTask = async (taskId, actualMinutes = null) => {
    try {
      const params = actualMinutes ? { actual_minutes: actualMinutes } : {}
      await axios.post(`/api/v1/coach/tasks/${taskId}/complete`, null, { params })
      await fetchBriefing() // Refresh briefing
    } catch (err) {
      console.error('Error completing task:', err)
      alert(err.response?.data?.detail || 'Failed to complete task')
    }
  }

  const updateTaskStatus = async (taskId, status) => {
    try {
      await axios.post(`/api/v1/coach/tasks/${taskId}/update`, {
        task_id: taskId,
        status: status
      })
      await fetchBriefing() // Refresh briefing
    } catch (err) {
      console.error('Error updating task:', err)
      alert(err.response?.data?.detail || 'Failed to update task')
    }
  }

  const openRescheduleModal = (task) => {
    setRescheduleModal({
      open: true,
      task: task,
      newDate: new Date().toISOString().split('T')[0]
    })
  }

  const rescheduleTask = async () => {
    try {
      await axios.post(`/api/v1/coach/tasks/${rescheduleModal.task.id}/reschedule`, {
        new_date: rescheduleModal.newDate,
        reason: 'User rescheduled'
      })
      setRescheduleModal({ open: false, task: null, newDate: '' })
      await fetchBriefing() // Refresh briefing
    } catch (err) {
      console.error('Error rescheduling task:', err)
      alert(err.response?.data?.detail || 'Failed to reschedule task')
    }
  }

  const autoReschedule = async () => {
    try {
      const response = await axios.post('/api/v1/coach/auto-reschedule', null, {
        params: { user_id: TEST_USER_ID }
      })
      alert(`Successfully rescheduled ${response.data.rescheduled_count} overdue task(s)`)
      await fetchBriefing() // Refresh briefing
    } catch (err) {
      console.error('Error auto-rescheduling:', err)
      alert(err.response?.data?.detail || 'Failed to auto-reschedule tasks')
    }
  }

  const carryOverTasks = async () => {
    try {
      const response = await axios.post('/api/v1/coach/carry-over', null, {
        params: {
          user_id: TEST_USER_ID,
          from_date: carryOverModal.fromDate,
          to_date: carryOverModal.toDate
        }
      })
      alert(`Successfully carried over ${response.data.total_carried_over} task(s)`)
      setCarryOverModal({ open: false, fromDate: '', toDate: '' })
      await fetchBriefing() // Refresh briefing
    } catch (err) {
      console.error('Error carrying over tasks:', err)
      alert(err.response?.data?.detail || 'Failed to carry over tasks')
    }
  }

  const enrichTasks = async () => {
    setEnriching(true)
    try {
      const response = await axios.post('/api/v1/coach/enrich-tasks', null, {
        params: { user_id: TEST_USER_ID }
      })
      alert(`Successfully enriched ${response.data.enriched_count} task(s) with study materials!`)
      await fetchBriefing() // Refresh briefing to show new content
    } catch (err) {
      console.error('Error enriching tasks:', err)
      alert(err.response?.data?.detail || 'Failed to enrich tasks')
    } finally {
      setEnriching(false)
    }
  }

  const startPomodoro = (taskId = null) => {
    setPomodoro(prev => ({
      ...prev,
      isRunning: true,
      isBreak: false,
      timeLeft: 25 * 60,
      currentTaskId: taskId
    }))
  }

  const pausePomodoro = () => {
    setPomodoro(prev => ({ ...prev, isRunning: false }))
  }

  const resetPomodoro = () => {
    setPomodoro(prev => ({
      ...prev,
      isRunning: false,
      isBreak: false,
      timeLeft: 25 * 60
    }))
  }

  const skipBreak = () => {
    setPomodoro(prev => ({
      ...prev,
      isBreak: false,
      isRunning: false,
      timeLeft: 25 * 60
    }))
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // OPTIMIZATION: Memoize task filtering - MUST be before conditional returns
  // Use safe access to avoid errors if briefing is null
  const overdueTasks = useMemo(() => 
    briefing?.tasks?.filter(t => t.is_overdue) || [], [briefing]
  )
  const pendingTasks = useMemo(() => 
    briefing?.tasks?.filter(t => !t.is_overdue && t.status === 'pending') || [], [briefing]
  )
  const inProgressTasks = useMemo(() => 
    briefing?.tasks?.filter(t => t.status === 'in_progress') || [], [briefing]
  )
  const completedTasks = useMemo(() => 
    briefing?.tasks?.filter(t => t.status === 'completed') || [], [briefing]
  )

  // Conditional returns - AFTER all hooks
  if (loading) {
    return (
      <div className="px-4 py-8">
        <div className="text-center">Loading daily briefing...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Error: {error}</p>
          <button
            onClick={fetchBriefing}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!briefing) {
    return (
      <div className="px-4 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-800 mb-4">
            No study plan found. Please generate one first!
          </p>
          <Link
            to="/upload"
            className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
          >
            Go to Upload Page
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Daily Coach</h1>
          <div className="flex gap-4">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2"
            />
            <button
              onClick={autoReschedule}
              disabled={overdueTasks.length === 0}
              className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Auto-Reschedule Overdue ({overdueTasks.length})
            </button>
            <button
              onClick={() => setCarryOverModal({ open: true, fromDate: selectedDate, toDate: selectedDate })}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Carry Over Tasks
            </button>
            <button
              onClick={enrichTasks}
              disabled={enriching}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {enriching ? 'Enriching...' : 'Add Study Materials'}
            </button>
          </div>
        </div>

        {/* Motivational Message */}
        {briefing.motivational_message && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-6">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <span className="text-2xl">💪</span>
              </div>
              <div className="ml-4">
                <p className="text-lg font-semibold text-gray-900 mb-1">Your Daily Motivation</p>
                <p className="text-gray-700">{briefing.motivational_message}</p>
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Total Tasks</p>
            <p className="text-2xl font-bold text-gray-900">{briefing.total_tasks}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-2xl font-bold text-green-600">{briefing.completed_tasks}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Pending</p>
            <p className="text-2xl font-bold text-yellow-600">{briefing.pending_tasks}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Overdue</p>
            <p className="text-2xl font-bold text-red-600">{briefing.overdue_tasks}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-gray-700">Today's Progress</span>
            <span className="text-sm font-bold text-primary-600">{briefing.completion_percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-primary-600 h-3 rounded-full transition-all"
              style={{ width: `${briefing.completion_percentage}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>Estimated: {Math.round(briefing.estimated_minutes / 60 * 10) / 10}h</span>
            {briefing.actual_minutes && (
              <span>Actual: {Math.round(briefing.actual_minutes / 60 * 10) / 10}h</span>
            )}
          </div>
        </div>

        {/* Pomodoro Timer */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-gray-900">🍅 Pomodoro Timer</h3>
            <div className="text-sm text-gray-600">
              Completed: {pomodoro.completedPomodoros} pomodoros
            </div>
          </div>
          
          <div className="flex items-center justify-center mb-4">
            <div className={`text-6xl font-bold ${
              pomodoro.isBreak ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatTime(pomodoro.timeLeft)}
            </div>
          </div>
          
          <div className="text-center mb-4">
            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
              pomodoro.isBreak 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {pomodoro.isBreak 
                ? (pomodoro.completedPomodoros % 4 === 0 ? '☕ Long Break (15 min)' : '☕ Short Break (5 min)')
                : '⏱️ Focus Time (25 min)'}
            </span>
          </div>
          
          <div className="flex justify-center gap-3 flex-wrap">
            {!pomodoro.isRunning ? (
              <button
                onClick={() => startPomodoro()}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 font-semibold"
              >
                {pomodoro.timeLeft === 25 * 60 && !pomodoro.isBreak ? 'Start Pomodoro' : 'Resume'}
              </button>
            ) : (
              <button
                onClick={pausePomodoro}
                className="bg-yellow-600 text-white px-6 py-2 rounded-lg hover:bg-yellow-700 font-semibold"
              >
                Pause
              </button>
            )}
            <button
              onClick={resetPomodoro}
              className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 font-semibold"
            >
              Reset
            </button>
            {pomodoro.isBreak && (
              <button
                onClick={skipBreak}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 font-semibold"
              >
                Skip Break
              </button>
            )}
          </div>
          
          {/* Pomodoro Progress Indicator */}
          {pomodoro.completedPomodoros > 0 && (
            <div className="mt-4">
              <div className="flex justify-center gap-2">
                {[...Array(Math.min(pomodoro.completedPomodoros, 8))].map((_, i) => (
                  <div
                    key={i}
                    className={`w-3 h-3 rounded-full ${
                      i < pomodoro.completedPomodoros ? 'bg-red-500' : 'bg-gray-300'
                    }`}
                    title={`Pomodoro ${i + 1}`}
                  />
                ))}
              </div>
              <p className="text-xs text-gray-500 text-center mt-2">
                {pomodoro.completedPomodoros >= 4 && (
                  <span className="text-green-600 font-semibold">
                    ✓ {Math.floor(pomodoro.completedPomodoros / 4)} full cycle{Math.floor(pomodoro.completedPomodoros / 4) > 1 ? 's' : ''} completed!
                  </span>
                )}
              </p>
            </div>
          )}
          
          {pomodoro.completedPomodoros > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600 text-center">
                🎉 Great work! You've completed {pomodoro.completedPomodoros} pomodoro{pomodoro.completedPomodoros !== 1 ? 's' : ''} today.
                {pomodoro.completedPomodoros >= 4 && (
                  <span className="block mt-1 text-green-600 font-semibold">
                    That's {Math.floor(pomodoro.completedPomodoros / 4)} full cycle{pomodoro.completedPomodoros >= 8 ? 's' : ''} (4 pomodoros = 1 cycle)!
                  </span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Current Week Progress */}
        {briefing.current_week && briefing.total_weeks && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 Week {briefing.current_week} of {briefing.total_weeks}</h3>
            {briefing.week_progress !== null && (
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-semibold text-gray-700">Week Progress</span>
                  <span className="text-sm font-bold text-primary-600">{briefing.week_progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-primary-600 h-3 rounded-full transition-all"
                    style={{ width: `${briefing.week_progress}%` }}
                  ></div>
                </div>
                {briefing.current_week < briefing.total_weeks && (
                  <p className="text-xs text-gray-500 mt-2">
                    Week {briefing.current_week + 1} starts when you complete this week's tasks
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Focus Skills */}
        {briefing.focus_skills && briefing.focus_skills.length > 0 && (
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Today's Focus Skills</h3>
            <div className="flex flex-wrap gap-2">
              {briefing.focus_skills.map((skill, idx) => (
                <span key={idx} className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Tasks (Next Week Preview) */}
        {briefing.upcoming_tasks && briefing.upcoming_tasks.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🔮 Upcoming Tasks (Next 7 Days)
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              {briefing.current_week && briefing.total_weeks && briefing.current_week < briefing.total_weeks
                ? `These tasks are coming up. Complete today's tasks to unlock Week ${briefing.current_week + 1}!`
                : "Here's what's coming up in the next few days:"}
            </p>
            <div className="space-y-3">
              {briefing.upcoming_tasks.slice(0, 5).map((task) => {
                const taskDate = task.task_date ? new Date(task.task_date) : new Date(selectedDate)
                const selectedDateObj = new Date(selectedDate)
                selectedDateObj.setHours(0, 0, 0, 0)
                taskDate.setHours(0, 0, 0, 0)
                const daysUntil = Math.ceil((taskDate - selectedDateObj) / (1000 * 60 * 60 * 24))
                const isNextWeek = daysUntil > 0 && briefing.current_week && briefing.current_week < briefing.total_weeks
                
                return (
                  <div key={task.id} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
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
                          <p className="font-medium text-gray-900 text-sm">{task.title}</p>
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
                        {isNextWeek && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-800">
                            Week {briefing.current_week + 1}
                          </span>
                        )}
                        {daysUntil > 0 && daysUntil <= 7 && (
                          <span className="text-xs text-gray-500">
                            {daysUntil === 1 ? 'Tomorrow' : `In ${daysUntil} days`}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
              {briefing.upcoming_tasks.length > 5 && (
                <p className="text-sm text-gray-500 text-center mt-2">
                  + {briefing.upcoming_tasks.length - 5} more upcoming tasks
                </p>
              )}
            </div>
          </div>
        )}

        {/* Overdue Tasks */}
        {overdueTasks.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-red-900 mb-4">
              ⚠️ Overdue Tasks ({overdueTasks.length})
            </h2>
            <div className="space-y-3">
              {overdueTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={() => completeTask(task.id)}
                  onReschedule={() => openRescheduleModal(task)}
                  onUpdateStatus={(status) => updateTaskStatus(task.id, status)}
                />
              ))}
            </div>
          </div>
        )}

        {/* In Progress Tasks */}
        {inProgressTasks.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              🔄 In Progress ({inProgressTasks.length})
            </h2>
            <div className="space-y-3">
              {inProgressTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={() => completeTask(task.id)}
                  onReschedule={() => openRescheduleModal(task)}
                  onUpdateStatus={(status) => updateTaskStatus(task.id, status)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Pending Tasks */}
        {pendingTasks.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              📋 Pending Tasks ({pendingTasks.length})
            </h2>
            <div className="space-y-3">
              {pendingTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={() => completeTask(task.id)}
                  onReschedule={() => openRescheduleModal(task)}
                  onUpdateStatus={(status) => updateTaskStatus(task.id, status)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              ✅ Completed Tasks ({completedTasks.length})
            </h2>
            <div className="space-y-3">
              {completedTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={() => completeTask(task.id)}
                  onReschedule={() => openRescheduleModal(task)}
                  onUpdateStatus={(status) => updateTaskStatus(task.id, status)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Reschedule Modal */}
        {rescheduleModal.open && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-semibold mb-4">Reschedule Task</h3>
              <p className="text-gray-700 mb-2">{rescheduleModal.task?.title}</p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Date
                </label>
                <input
                  type="date"
                  value={rescheduleModal.newDate}
                  onChange={(e) => setRescheduleModal({ ...rescheduleModal, newDate: e.target.value })}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={rescheduleTask}
                  className="flex-1 bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
                >
                  Reschedule
                </button>
                <button
                  onClick={() => setRescheduleModal({ open: false, task: null, newDate: '' })}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Carry Over Modal */}
        {carryOverModal.open && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-semibold mb-4">Carry Over Tasks</h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  From Date
                </label>
                <input
                  type="date"
                  value={carryOverModal.fromDate}
                  onChange={(e) => setCarryOverModal({ ...carryOverModal, fromDate: e.target.value })}
                  className="w-full border border-gray-300 rounded px-3 py-2 mb-3"
                />
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  To Date
                </label>
                <input
                  type="date"
                  value={carryOverModal.toDate}
                  onChange={(e) => setCarryOverModal({ ...carryOverModal, toDate: e.target.value })}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={carryOverTasks}
                  className="flex-1 bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
                >
                  Carry Over
                </button>
                <button
                  onClick={() => setCarryOverModal({ open: false, fromDate: '', toDate: '' })}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Task Card Component
function TaskCard({ task, onComplete, onReschedule, onUpdateStatus }) {
  const [expanded, setExpanded] = useState(false)
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-yellow-100 text-yellow-800'
      case 'skipped': return 'bg-gray-100 text-gray-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'learn': return 'bg-blue-100 text-blue-800'
      case 'practice': return 'bg-green-100 text-green-800'
      case 'review': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const content = task.content || {}
  const studyMaterials = content.study_materials || []
  const resources = content.resources || []
  const keyConcepts = content.key_concepts || []
  const practiceExercises = content.practice_exercises || []

  return (
    <div className={`border rounded-lg p-4 ${task.is_overdue ? 'border-red-300 bg-red-50' : 'border-gray-200'} hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getTypeColor(task.task_type)}`}>
              {task.task_type}
            </span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(task.status)}`}>
              {task.status}
            </span>
            {task.is_overdue && (
              <span className="px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-800">
                {task.days_overdue} day{task.days_overdue !== 1 ? 's' : ''} overdue
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-gray-900">{task.title}</h3>
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              {expanded ? '▼ Hide Details' : '▶ View Study Materials'}
            </button>
          </div>
          <p className="text-sm text-gray-600 mb-2">{task.description}</p>
          
          {/* Expanded Content */}
          {expanded && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
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
                  <ul className="space-y-2">
                    {resources.map((resource, idx) => (
                      <li key={idx}>
                        <a
                          href={resource}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 hover:underline text-sm flex items-center"
                        >
                          <span className="mr-1">→</span>
                          {resource}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Practice Exercises */}
              {practiceExercises.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                    <span className="mr-2">✏️</span> Practice Exercises
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                    {practiceExercises.map((exercise, idx) => (
                      <li key={idx}>{exercise}</li>
                    ))}
                  </ul>
                </div>
              )}

              {studyMaterials.length === 0 && resources.length === 0 && keyConcepts.length === 0 && practiceExercises.length === 0 && (
                <p className="text-sm text-gray-500 italic">No additional study materials provided for this task.</p>
              )}
            </div>
          )}

          {task.skill_names && task.skill_names.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {task.skill_names.map((skill, idx) => (
                <span key={idx} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                  {skill}
                </span>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-500">Estimated: {task.estimated_minutes} minutes</p>
        </div>
        <div className="flex flex-col gap-2 ml-4">
          {task.status !== 'completed' && (
            <>
              <button
                onClick={() => {
                  startPomodoro(task.id)
                  onUpdateStatus('in_progress')
                }}
                className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                title="Start Pomodoro for this task"
              >
                🍅 Start Pomodoro
              </button>
              <button
                onClick={onComplete}
                className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
              >
                Complete
              </button>
              {task.status === 'pending' && (
                <button
                  onClick={() => onUpdateStatus('in_progress')}
                  className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                >
                  Start
                </button>
              )}
              <button
                onClick={onReschedule}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
              >
                Reschedule
              </button>
              <button
                onClick={() => onUpdateStatus('skipped')}
                className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700"
              >
                Skip
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default DailyCoach

