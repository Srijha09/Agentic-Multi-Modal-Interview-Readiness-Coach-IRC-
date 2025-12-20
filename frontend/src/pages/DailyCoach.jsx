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
  const [practiceItems, setPracticeItems] = useState({}) // task_id -> [practice items]
  const [generatingPractice, setGeneratingPractice] = useState({}) // task_id -> practice_type
  const [selectedPracticeItem, setSelectedPracticeItem] = useState(null) // For viewing/taking practice
  const [practiceAnswers, setPracticeAnswers] = useState({}) // practice_item_id -> answer
  const [evaluationResults, setEvaluationResults] = useState({}) // practice_item_id -> evaluation
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

  // Fetch practice items for tasks when briefing loads
  useEffect(() => {
    if (briefing && briefing.tasks) {
      fetchPracticeItemsForTasks(briefing.tasks.map(t => t.id))
    }
  }, [briefing])

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

  // Phase 7: Practice Items Functions
  const fetchPracticeItemsForTasks = async (taskIds) => {
    try {
      const itemsByTask = {}
      for (const taskId of taskIds) {
        try {
          const response = await axios.get(`/api/v1/practice/items/task/${taskId}`)
          itemsByTask[taskId] = response.data
        } catch (err) {
          // Task might not have practice items yet
          itemsByTask[taskId] = []
        }
      }
      setPracticeItems(itemsByTask)
    } catch (err) {
      console.error('Error fetching practice items:', err)
    }
  }

  const generatePracticeItems = async (taskId, practiceType, count = 1) => {
    setGeneratingPractice(prev => ({ ...prev, [taskId]: practiceType }))
    try {
      const response = await axios.post(
        `/api/v1/practice/items/generate?task_id=${taskId}&practice_type=${practiceType}&count=${count}`
      )
      
      // Update practice items for this task
      setPracticeItems(prev => ({
        ...prev,
        [taskId]: [...(prev[taskId] || []), ...response.data]
      }))
      
      alert(`Successfully generated ${response.data.length} ${practiceType} item(s)!`)
    } catch (err) {
      console.error('Error generating practice items:', err)
      alert(err.response?.data?.detail || 'Failed to generate practice items')
    } finally {
      setGeneratingPractice(prev => {
        const next = { ...prev }
        delete next[taskId]
        return next
      })
    }
  }

  const submitPracticeAttempt = async (practiceItemId, answer, timeSpentSeconds = null, taskId = null) => {
    try {
      // Get task_id from parameter (passed from modal) or from selectedPracticeItem if available
      const finalTaskId = taskId || null
      
      console.log('Submitting practice attempt:', {
        practice_item_id: practiceItemId,
        user_id: TEST_USER_ID,
        answer: answer,
        time_spent_seconds: timeSpentSeconds,
        task_id: finalTaskId
      })
      
      const response = await axios.post('/api/v1/practice/attempts/submit', {
        practice_item_id: practiceItemId,
        user_id: TEST_USER_ID,
        answer: answer,
        time_spent_seconds: timeSpentSeconds,
        task_id: finalTaskId
      })
      
      // Phase 8: Store evaluation results if available
      if (response.data.evaluation) {
        setEvaluationResults(prev => ({
          ...prev,
          [practiceItemId]: response.data.evaluation
        }))
      }
      
      // Don't close modal immediately - show evaluation results
      // setSelectedPracticeItem(null)
      setPracticeAnswers(prev => {
        const next = { ...prev }
        delete next[practiceItemId]
        return next
      })
      
      return response.data
    } catch (err) {
      console.error('Error submitting practice attempt:', err)
      console.error('Error response:', err.response)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to submit practice attempt'
      alert(`Error: ${errorMessage}`)
      throw err
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
                  practiceItems={practiceItems[task.id] || []}
                  onGeneratePractice={generatePracticeItems}
                  generatingPractice={generatingPractice[task.id]}
                  onViewPractice={setSelectedPracticeItem}
                  onStartPomodoro={startPomodoro}
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
                  practiceItems={practiceItems[task.id] || []}
                  onGeneratePractice={generatePracticeItems}
                  generatingPractice={generatingPractice[task.id]}
                  onViewPractice={setSelectedPracticeItem}
                  onStartPomodoro={startPomodoro}
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
                  practiceItems={practiceItems[task.id] || []}
                  onGeneratePractice={generatePracticeItems}
                  generatingPractice={generatingPractice[task.id]}
                  onViewPractice={setSelectedPracticeItem}
                  onStartPomodoro={startPomodoro}
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
                  practiceItems={practiceItems[task.id] || []}
                  onGeneratePractice={generatePracticeItems}
                  generatingPractice={generatingPractice[task.id]}
                  onViewPractice={setSelectedPracticeItem}
                  onStartPomodoro={startPomodoro}
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

        {/* Practice Item Modal - Phase 7 */}
        {selectedPracticeItem && selectedPracticeItem.id && (
          <PracticeItemModal
            key={selectedPracticeItem.id}
            item={selectedPracticeItem}
            onClose={() => setSelectedPracticeItem(null)}
            onSubmit={async (practiceItemId, answer, timeSpentSeconds, taskId) => {
              return await submitPracticeAttempt(practiceItemId, answer, timeSpentSeconds, taskId)
            }}
            answer={practiceAnswers[selectedPracticeItem.id] || ''}
            onAnswerChange={(answer) => {
              const itemId = selectedPracticeItem.id
              setPracticeAnswers(prev => ({ ...prev, [itemId]: answer }))
            }}
            evaluation={evaluationResults[selectedPracticeItem.id]}
          />
        )}
      </div>
    </div>
  )
}

// Task Card Component
function TaskCard({ 
  task, 
  onComplete, 
  onReschedule, 
  onUpdateStatus,
  practiceItems = [],
  onGeneratePractice,
  generatingPractice = null,
  onViewPractice,
  onStartPomodoro
}) {
  const [expanded, setExpanded] = useState(false)
  const [showPracticeSection, setShowPracticeSection] = useState(false)
  
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

              {/* Practice Items Section - Phase 7 */}
              <div className="mt-4 pt-4 border-t border-gray-300">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <span className="mr-2">🎯</span> Practice Items
                  </h4>
                  <button
                    onClick={() => setShowPracticeSection(!showPracticeSection)}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    {showPracticeSection ? '▼ Hide' : '▶ Show'}
                  </button>
                </div>

                {showPracticeSection && (
                  <div className="space-y-3">
                    {/* Generate Practice Buttons */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      <button
                        onClick={() => onGeneratePractice(task.id, 'quiz', 1)}
                        disabled={generatingPractice === 'quiz'}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 disabled:bg-gray-300"
                      >
                        {generatingPractice === 'quiz' ? 'Generating...' : '📝 Generate Quiz'}
                      </button>
                      <button
                        onClick={() => onGeneratePractice(task.id, 'flashcard', 2)}
                        disabled={generatingPractice === 'flashcard'}
                        className="bg-purple-600 text-white px-3 py-1 rounded text-xs hover:bg-purple-700 disabled:bg-gray-300"
                      >
                        {generatingPractice === 'flashcard' ? 'Generating...' : '🃏 Generate Flashcards'}
                      </button>
                      <button
                        onClick={() => onGeneratePractice(task.id, 'behavioral', 1)}
                        disabled={generatingPractice === 'behavioral'}
                        className="bg-orange-600 text-white px-3 py-1 rounded text-xs hover:bg-orange-700 disabled:bg-gray-300"
                      >
                        {generatingPractice === 'behavioral' ? 'Generating...' : '💬 Generate Behavioral Q'}
                      </button>
                      <button
                        onClick={() => onGeneratePractice(task.id, 'system_design', 1)}
                        disabled={generatingPractice === 'system_design'}
                        className="bg-indigo-600 text-white px-3 py-1 rounded text-xs hover:bg-indigo-700 disabled:bg-gray-300"
                      >
                        {generatingPractice === 'system_design' ? 'Generating...' : '🏗️ Generate System Design'}
                      </button>
                    </div>

                    {/* Display Practice Items */}
                    {practiceItems.length === 0 ? (
                      <p className="text-sm text-gray-500 italic">No practice items yet. Generate some above!</p>
                    ) : (
                      <div className="space-y-2">
                        {practiceItems.map((item) => (
                          <PracticeItemCard
                            key={item.id}
                            item={item}
                            onView={() => onViewPractice(item)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
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
                  if (onStartPomodoro) onStartPomodoro(task.id)
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

// Practice Item Card Component (shows in task card)
function PracticeItemCard({ item, onView }) {
  const getTypeIcon = (type) => {
    switch (type) {
      case 'quiz': return '📝'
      case 'flashcard': return '🃏'
      case 'behavioral': return '💬'
      case 'system_design': return '🏗️'
      default: return '📋'
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'quiz': return 'bg-blue-100 text-blue-800'
      case 'flashcard': return 'bg-purple-100 text-purple-800'
      case 'behavioral': return 'bg-orange-100 text-orange-800'
      case 'system_design': return 'bg-indigo-100 text-indigo-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="border border-gray-300 rounded p-2 bg-white hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1">
          <span className="text-lg">{getTypeIcon(item.practice_type)}</span>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm text-gray-900 truncate">{item.title}</p>
            <p className="text-xs text-gray-600 truncate">{item.question.substring(0, 60)}...</p>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getTypeColor(item.practice_type)}`}>
            {item.difficulty}
          </span>
        </div>
        <button
          onClick={() => onView(item)}
          className="ml-2 bg-primary-600 text-white px-3 py-1 rounded text-xs hover:bg-primary-700"
        >
          View
        </button>
      </div>
    </div>
  )
}

// Evaluation Display Component (Phase 8)
function EvaluationDisplay({ evaluation, onClose }) {
  if (!evaluation) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Evaluation loading...</p>
      </div>
    )
  }

  const scorePercentage = Math.round(evaluation.overall_score * 100)
  const scoreColor = 
    scorePercentage >= 80 ? 'text-green-600' :
    scorePercentage >= 60 ? 'text-yellow-600' :
    'text-red-600'

  return (
    <div className="space-y-6">
      {/* Score Header */}
      <div className="text-center">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Your Results</h3>
        <div className="flex items-center justify-center gap-4">
          <div className={`text-5xl font-bold ${scoreColor}`}>
            {scorePercentage}%
          </div>
          <div className="text-left">
            <p className="text-sm text-gray-600">Overall Score</p>
            <p className="text-xs text-gray-500">
              {evaluation.overall_score.toFixed(2)} / 1.0
            </p>
          </div>
        </div>
      </div>

      {/* Criterion Scores */}
      {evaluation.criterion_scores && Object.keys(evaluation.criterion_scores).length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Detailed Scores</h4>
          <div className="space-y-2">
            {Object.entries(evaluation.criterion_scores).map(([criterion, score]) => {
              const criterionPercentage = Math.round(score * 100)
              return (
                <div key={criterion} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{criterion}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${criterionPercentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-900 w-12 text-right">
                      {criterionPercentage}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Strengths */}
      {evaluation.strengths && evaluation.strengths.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-2 flex items-center">
            <span className="mr-2">✓</span> Strengths
          </h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-green-800">
            {evaluation.strengths.map((strength, idx) => (
              <li key={idx}>{strength}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Weaknesses */}
      {evaluation.weaknesses && evaluation.weaknesses.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h4 className="font-semibold text-orange-900 mb-2 flex items-center">
            <span className="mr-2">⚠</span> Areas for Improvement
          </h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-orange-800">
            {evaluation.weaknesses.map((weakness, idx) => (
              <li key={idx}>{weakness}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Feedback */}
      {evaluation.feedback && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">Feedback</h4>
          <p className="text-sm text-blue-800 whitespace-pre-wrap">
            {evaluation.feedback}
          </p>
        </div>
      )}

      {/* Close Button */}
      <div className="flex justify-end">
        <button
          onClick={onClose}
          className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 font-semibold"
        >
          Close
        </button>
      </div>
    </div>
  )
}

// Practice Item Modal Component (for taking quizzes, viewing flashcards, etc.)
function PracticeItemModal({ item, onClose, onSubmit, answer, onAnswerChange, evaluation }) {
  const [submitting, setSubmitting] = useState(false)
  const [startTime] = useState(Date.now())
  const [currentEvaluation, setCurrentEvaluation] = useState(evaluation)
  
  // Update evaluation when prop changes
  useEffect(() => {
    if (evaluation) {
      setCurrentEvaluation(evaluation)
    }
  }, [evaluation])

  const handleSubmit = async (overrideAnswer = null) => {
    const answerToSubmit = overrideAnswer !== null ? overrideAnswer : answer
    if (!answerToSubmit || !answerToSubmit.trim()) {
      alert('Please provide an answer')
      return
    }

    setSubmitting(true)
    try {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000)
      const taskId = item.task_id || null
      const result = await onSubmit(item.id, answerToSubmit, timeSpent, taskId)
      // Show evaluation if available
      if (result && result.evaluation) {
        setCurrentEvaluation(result.evaluation)
      }
    } catch (err) {
      // Error already handled in parent
    } finally {
      setSubmitting(false)
    }
  }

  const renderQuiz = () => {
    const options = item.content?.options || []
    const isMCQ = options.length > 0

    return (
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Question:</h3>
          <p className="text-gray-700">{item.question}</p>
        </div>

        {isMCQ ? (
          <div className="space-y-2">
            <p className="font-semibold text-gray-900">Select your answer:</p>
            {options.map((option, idx) => {
              const optionLabel = String.fromCharCode(65 + idx) // A, B, C, D
              return (
                <label
                  key={idx}
                  className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                    answer === optionLabel
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="quiz-answer"
                    value={optionLabel}
                    checked={answer === optionLabel}
                    onChange={(e) => onAnswerChange(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-semibold text-gray-700 mr-2">{optionLabel}.</span>
                  <span className="text-gray-700">{option}</span>
                </label>
              )
            })}
          </div>
        ) : (
          <div>
            <label className="block font-semibold text-gray-900 mb-2">Your answer:</label>
            <textarea
              value={answer}
              onChange={(e) => onAnswerChange(e.target.value)}
              placeholder="Type your answer here..."
              className="w-full border border-gray-300 rounded-lg p-3 min-h-[150px] focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            {item.content?.key_points && item.content.key_points.length > 0 && (
              <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm font-semibold text-gray-900 mb-1">Key points to include:</p>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {item.content.key_points.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderFlashcard = () => {
    const [showAnswer, setShowAnswer] = useState(false)

    return (
      <div className="space-y-4">
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 min-h-[200px] flex items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-900 mb-2">Front:</p>
            <p className="text-xl text-gray-700">{item.question}</p>
          </div>
        </div>

        <button
          onClick={() => setShowAnswer(!showAnswer)}
          className="w-full bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 font-semibold"
        >
          {showAnswer ? 'Hide Answer' : 'Show Answer'}
        </button>

        {showAnswer && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <p className="text-lg font-semibold text-gray-900 mb-2">Back:</p>
            <p className="text-xl text-gray-700">{item.content?.back || item.expected_answer}</p>
          </div>
        )}

        <div className="mt-4">
          <label className="block font-semibold text-gray-900 mb-2">Did you get it right?</label>
          <div className="flex gap-2">
            <button
              onClick={() => {
                onAnswerChange('correct')
                handleSubmit('correct')
              }}
              disabled={submitting}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-300"
            >
              ✓ Correct
            </button>
            <button
              onClick={() => {
                onAnswerChange('incorrect')
                handleSubmit('incorrect')
              }}
              disabled={submitting}
              className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:bg-gray-300"
            >
              ✗ Incorrect
            </button>
          </div>
        </div>
      </div>
    )
  }

  const renderBehavioral = () => {
    const starGuidance = item.content?.star_guidance || {}
    const criteria = item.content?.evaluation_criteria || []

    return (
      <div className="space-y-4">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Question:</h3>
          <p className="text-gray-700 text-lg">{item.question}</p>
        </div>

        {starGuidance && Object.keys(starGuidance).length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-3">STAR Method Guidance:</h4>
            <div className="space-y-2 text-sm">
              {starGuidance.situation && (
                <div>
                  <span className="font-semibold text-gray-900">Situation:</span>
                  <p className="text-gray-700 ml-2">{starGuidance.situation}</p>
                </div>
              )}
              {starGuidance.task && (
                <div>
                  <span className="font-semibold text-gray-900">Task:</span>
                  <p className="text-gray-700 ml-2">{starGuidance.task}</p>
                </div>
              )}
              {starGuidance.action && (
                <div>
                  <span className="font-semibold text-gray-900">Action:</span>
                  <p className="text-gray-700 ml-2">{starGuidance.action}</p>
                </div>
              )}
              {starGuidance.result && (
                <div>
                  <span className="font-semibold text-gray-900">Result:</span>
                  <p className="text-gray-700 ml-2">{starGuidance.result}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {criteria.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Evaluation Criteria:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {criteria.map((criterion, idx) => (
                <li key={idx}>{criterion}</li>
              ))}
            </ul>
          </div>
        )}

        <div>
          <label className="block font-semibold text-gray-900 mb-2">Your STAR response:</label>
          <textarea
            value={answer}
            onChange={(e) => onAnswerChange(e.target.value)}
            placeholder="Describe the Situation, Task, Action, and Result..."
            className="w-full border border-gray-300 rounded-lg p-3 min-h-[200px] focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>
    )
  }

  const renderSystemDesign = () => {
    const requirements = item.content?.requirements || []
    const constraints = item.content?.constraints || []
    const framework = item.content?.evaluation_framework || {}

    return (
      <div className="space-y-4">
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Challenge:</h3>
          <p className="text-gray-700 text-lg">{item.question}</p>
        </div>

        {requirements.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Requirements:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {requirements.map((req, idx) => (
                <li key={idx}>{req}</li>
              ))}
            </ul>
          </div>
        )}

        {constraints.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Constraints:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {constraints.map((constraint, idx) => (
                <li key={idx}>{constraint}</li>
              ))}
            </ul>
          </div>
        )}

        {framework && Object.keys(framework).length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Evaluation Framework:</h4>
            <div className="space-y-2 text-sm">
              {framework.functional_requirements && (
                <div>
                  <span className="font-semibold">Functional:</span>
                  <ul className="list-disc list-inside ml-2 text-gray-700">
                    {framework.functional_requirements.map((req, idx) => (
                      <li key={idx}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}
              {framework.non_functional_requirements && (
                <div>
                  <span className="font-semibold">Non-functional:</span>
                  <ul className="list-disc list-inside ml-2 text-gray-700">
                    {framework.non_functional_requirements.map((req, idx) => (
                      <li key={idx}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        <div>
          <label className="block font-semibold text-gray-900 mb-2">Your system design:</label>
          <textarea
            value={answer}
            onChange={(e) => onAnswerChange(e.target.value)}
            placeholder="Describe your system architecture, components, data flow, and trade-offs..."
            className="w-full border border-gray-300 rounded-lg p-3 min-h-[250px] focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>
    )
  }

  const renderContent = () => {
    switch (item.practice_type) {
      case 'quiz':
        return renderQuiz()
      case 'flashcard':
        return renderFlashcard()
      case 'behavioral':
        return renderBehavioral()
      case 'system_design':
        return renderSystemDesign()
      default:
        return <p className="text-gray-700">{item.question}</p>
    }
  }

  const getTypeTitle = () => {
    switch (item.practice_type) {
      case 'quiz': return 'Quiz'
      case 'flashcard': return 'Flashcard'
      case 'behavioral': return 'Behavioral Interview Question'
      case 'system_design': return 'System Design Challenge'
      default: return 'Practice Item'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{item.title}</h2>
            <p className="text-sm text-gray-600">
              {getTypeTitle()} • {item.difficulty} • {item.skill_names?.join(', ') || 'General'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {!currentEvaluation ? (
            <>
              {renderContent()}

              {item.practice_type !== 'flashcard' && (
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || !answer.trim()}
                    className="flex-1 bg-primary-600 text-white px-4 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                  >
                    {submitting ? 'Submitting...' : 'Submit Answer'}
                  </button>
                  <button
                    onClick={onClose}
                    className="bg-gray-300 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-400 font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </>
          ) : (
            <EvaluationDisplay 
              evaluation={currentEvaluation}
              onClose={onClose}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default DailyCoach

