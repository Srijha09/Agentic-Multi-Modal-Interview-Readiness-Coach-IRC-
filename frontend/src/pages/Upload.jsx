import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function Upload() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [analysisStartTime, setAnalysisStartTime] = useState(null)
  const [message, setMessage] = useState('')
  const [uploadResult, setUploadResult] = useState(null)
  const [gapReport, setGapReport] = useState(null)
  const [studyPlan, setStudyPlan] = useState(null)
  const [generatingPlan, setGeneratingPlan] = useState(false)
  const progressIntervalRef = useRef(null)
  
  // For testing - use the user_id from create_test_user.py (typically 1)
  const TEST_USER_ID = 1
  
  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [])

  const handleResumeChange = (e) => {
    setResumeFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setUploading(true)
    setMessage('')
    setUploadResult(null)

    try {
      let resumeDocId = null
      let jdDocId = null
      
      // Upload resume if provided
      if (resumeFile) {
        const formData = new FormData()
        formData.append('file', resumeFile)
        formData.append('document_type', 'resume')
        formData.append('user_id', TEST_USER_ID.toString())

        const response = await axios.post('/api/v1/documents/upload', formData)
        resumeDocId = response.data.id
        
        setUploadResult(prev => ({
          ...prev,
          data: response.data
        }))
        setMessage(`✓ Resume uploaded successfully! Document ID: ${response.data.id}`)
      }

      // Handle job description text
      if (jobDescription.trim()) {
        // Convert text to a Blob and upload as file
        const blob = new Blob([jobDescription], { type: 'text/plain' })
        const jdFile = new File([blob], 'job_description.txt', { type: 'text/plain' })
        
        const formData = new FormData()
        formData.append('file', jdFile)
        formData.append('document_type', 'job_description')
        formData.append('user_id', TEST_USER_ID.toString())

        const response = await axios.post('/api/v1/documents/upload', formData)
        jdDocId = response.data.id
        
        setUploadResult(prev => ({
          ...prev,
          jd: response.data
        }))
        setMessage(prev => prev 
          ? `${prev}\n✓ Job description uploaded! Document ID: ${response.data.id}`
          : `✓ Job description uploaded! Document ID: ${response.data.id}`
        )
      }

      if (!resumeFile && !jobDescription.trim()) {
        setMessage('Please upload a resume or enter a job description.')
      }

      setUploading(false)
      
      // Automatically trigger gap analysis if both documents are uploaded
      if (resumeDocId && jdDocId) {
        await analyzeGaps(resumeDocId, jdDocId)
      }
    } catch (error) {
      console.error('Upload error:', error)
      setMessage(
        error.response?.data?.detail || 
        error.message || 
        'Error uploading file. Please try again.'
      )
      setUploading(false)
    }
  }

  const analyzeGaps = async (resumeDocId, jdDocId) => {
    const startTime = Date.now()
    setAnalyzing(true)
    setAnalysisProgress(0)
    setAnalysisStartTime(startTime)
    setMessage(prev => prev + '\n\n⏳ Analyzing skill gaps... This may take a minute.')
    
    // Simulate progress (since we can't track real progress from backend)
    // Estimate: 60 seconds total, update every 500ms
    progressIntervalRef.current = setInterval(() => {
      setAnalysisProgress(prev => {
        // Gradually increase progress, but cap at 90% until we get response
        const elapsed = (Date.now() - startTime) / 1000
        const estimatedTotal = 60 // 60 seconds estimated
        const progress = Math.min((elapsed / estimatedTotal) * 90, 90)
        return Math.floor(progress)
      })
    }, 500)
    
    try {
      console.log('Starting gap analysis:', { resumeDocId, jdDocId, userId: TEST_USER_ID })
      
      // Use query parameters for the POST request
      const response = await axios.post(
        `/api/v1/gaps/analyze?user_id=${TEST_USER_ID}&resume_document_id=${resumeDocId}&jd_document_id=${jdDocId}`
      )
      
      console.log('Gap analysis response:', response.data)
      
      // Complete the progress bar
      setAnalysisProgress(100)
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      
      // Small delay to show 100% before hiding
      setTimeout(() => {
        setGapReport(response.data)
        setMessage(prev => {
          const base = prev.split('\n\n')[0] // Keep original upload messages
          return `${base}\n\n✓ Gap analysis complete! Found ${response.data.total_gaps} skill gaps (${response.data.critical_gaps} critical, ${response.data.high_priority_gaps} high priority).`
        })
        setAnalyzing(false)
      }, 500)
    } catch (error) {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      console.error('Gap analysis error:', error)
      console.error('Error response:', error.response)
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
      setMessage(prev => {
        const base = prev.split('\n\n')[0] // Keep original upload messages
        return `${base}\n\n✗ Error analyzing gaps: ${errorMsg}\n\nPlease check:\n1. LLM API key is set in backend .env\n2. Backend server is running\n3. Check browser console (F12) for details`
      })
      setAnalyzing(false)
      setAnalysisProgress(0)
    }
  }

  const generateStudyPlan = async (weeks, hoursPerWeek) => {
    setGeneratingPlan(true)
    setMessage(prev => prev + `\n\n📅 Generating ${weeks}-week study plan...`)
    
    try {
      console.log('Generating study plan:', { userId: TEST_USER_ID, weeks, hoursPerWeek })
      
      const response = await axios.post(
        `/api/v1/plans/generate?user_id=${TEST_USER_ID}&weeks=${weeks}&hours_per_week=${hoursPerWeek}`
      )
      
      console.log('Study plan response:', response.data)
      
      setStudyPlan(response.data)
      setMessage(prev => {
        const base = prev.split('\n\n')[0]
        return `${base}\n\n✓ Study plan generated! ${weeks} weeks with ${hoursPerWeek}h/week.`
      })
    } catch (error) {
      console.error('Plan generation error:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
      setMessage(prev => {
        const base = prev.split('\n\n')[0]
        return `${base}\n\n✗ Error generating plan: ${errorMsg}`
      })
    } finally {
      setGeneratingPlan(false)
    }
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Upload Documents</h1>
        
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resume (PDF or DOCX)
            </label>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleResumeChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-primary-50 file:text-primary-700
                hover:file:bg-primary-100"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Paste the job description here..."
            />
          </div>

          <button
            type="submit"
            disabled={uploading || (!resumeFile && !jobDescription)}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {uploading ? 'Uploading...' : 'Upload & Analyze'}
          </button>

          {message && (
            <div className={`mt-4 p-3 rounded ${
              message.includes('Error') || message.includes('Please')
                ? 'bg-red-50 text-red-700' 
                : 'bg-green-50 text-green-700'
            }`}>
              {message.split('\n').map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          )}

          {uploadResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold mb-2 text-gray-900">Upload Results:</h3>
              {uploadResult.data && (
                <div className="mb-2">
                  <p className="text-sm text-gray-700">
                    <strong>Resume:</strong> Document ID {uploadResult.data.id}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Sections: {uploadResult.data.doc_metadata?.section_count || 0} | 
                    Chunks: {uploadResult.data.doc_metadata?.chunk_count || 0} |
                    Characters: {uploadResult.data.doc_metadata?.char_count || 0}
                  </p>
                </div>
              )}
              {uploadResult.jd && (
                <div>
                  <p className="text-sm text-gray-700">
                    <strong>Job Description:</strong> Document ID {uploadResult.jd.id}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Sections: {uploadResult.jd.doc_metadata?.section_count || 0} | 
                    Chunks: {uploadResult.jd.doc_metadata?.chunk_count || 0} |
                    Characters: {uploadResult.jd.doc_metadata?.char_count || 0}
                  </p>
                </div>
              )}
            </div>
          )}

          {uploadResult?.data && uploadResult?.jd && !gapReport && !analyzing && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 mb-3">
                Documents uploaded successfully! Click below to analyze skill gaps.
              </p>
              <button
                type="button"
                onClick={() => analyzeGaps(uploadResult.data.id, uploadResult.jd.id)}
                className="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700 font-semibold"
              >
                🔍 Analyze Skill Gaps
              </button>
            </div>
          )}

          {analyzing && (
            <div className="mt-4 p-4 bg-blue-50 text-blue-700 rounded-lg border border-blue-200">
              <div className="flex justify-between items-center mb-2">
                <p className="font-semibold">⏳ Analyzing skill gaps...</p>
                <p className="text-sm font-semibold">{analysisProgress}%</p>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-blue-200 rounded-full h-3 mb-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${analysisProgress}%` }}
                ></div>
              </div>
              
              {/* Status Messages */}
              <div className="text-sm space-y-1">
                {analysisProgress < 20 && (
                  <p>📄 Extracting skills from resume...</p>
                )}
                {analysisProgress >= 20 && analysisProgress < 40 && (
                  <p>📋 Extracting requirements from job description...</p>
                )}
                {analysisProgress >= 40 && analysisProgress < 70 && (
                  <p>🔍 Comparing skills and identifying gaps...</p>
                )}
                {analysisProgress >= 70 && analysisProgress < 100 && (
                  <p>📊 Prioritizing gaps and generating report...</p>
                )}
                {analysisProgress === 100 && (
                  <p className="text-green-600 font-semibold">✓ Analysis complete!</p>
                )}
              </div>
              
              {/* Time Estimate */}
              {analysisStartTime && analysisProgress < 100 && (
                <p className="text-xs text-blue-600 mt-2">
                  Estimated time remaining: {Math.max(0, Math.ceil((60 * (100 - analysisProgress)) / 100))}s
                </p>
              )}
            </div>
          )}

          {gapReport && (
            <div className="mt-6 p-6 bg-white rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Skill Gap Analysis Report</h2>
              
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Total Gaps</p>
                  <p className="text-2xl font-bold text-red-600">{gapReport.total_gaps}</p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Critical</p>
                  <p className="text-2xl font-bold text-orange-600">{gapReport.critical_gaps}</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">High Priority</p>
                  <p className="text-2xl font-bold text-yellow-600">{gapReport.high_priority_gaps}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Covered Skills</p>
                  <p className="text-2xl font-bold text-green-600">
                    {gapReport.gaps.filter(g => g.coverage_status === 'covered').length}
                  </p>
                </div>
              </div>

              {/* Gap List */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Skill Gaps (Prioritized)</h3>
                
                {gapReport.gaps
                  .sort((a, b) => {
                    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
                    return priorityOrder[a.priority] - priorityOrder[b.priority]
                  })
                  .map((gap) => {
                    const priorityColors = {
                      critical: 'bg-red-100 border-red-300 text-red-800',
                      high: 'bg-orange-100 border-orange-300 text-orange-800',
                      medium: 'bg-yellow-100 border-yellow-300 text-yellow-800',
                      low: 'bg-blue-100 border-blue-300 text-blue-800'
                    }
                    
                    const coverageColors = {
                      missing: 'text-red-600 font-semibold',
                      partial: 'text-yellow-600 font-semibold',
                      covered: 'text-green-600 font-semibold'
                    }
                    
                    return (
                      <div key={gap.id} className={`border-2 rounded-lg p-4 ${priorityColors[gap.priority]}`}>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-bold text-lg">{gap.required_skill_name}</h4>
                            <p className="text-sm mt-1">
                              <span className={coverageColors[gap.coverage_status]}>
                                {gap.coverage_status.toUpperCase()}
                              </span>
                              {' • '}
                              <span className="font-semibold">{gap.priority.toUpperCase()} Priority</span>
                            </p>
                          </div>
                          {gap.estimated_learning_hours > 0 && (
                            <div className="text-right">
                              <p className="text-sm font-semibold">{gap.estimated_learning_hours}h</p>
                              <p className="text-xs text-gray-600">estimated</p>
                            </div>
                          )}
                        </div>
                        
                        <p className="text-sm mt-2 mb-2">{gap.gap_reason}</p>
                        
                        {gap.evidence && gap.evidence.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-300">
                            <p className="text-xs font-semibold mb-1">Evidence:</p>
                            {gap.evidence.map((ev, idx) => (
                              <p key={idx} className="text-xs italic text-gray-700 mb-1">
                                "{ev.evidence_text}"
                                {ev.section_name && <span className="ml-1">({ev.section_name})</span>}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {gapReport && !studyPlan && !generatingPlan && (
            <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="text-sm text-purple-800 mb-3">
                Skill gaps identified! Generate a personalized study plan to address them.
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => generateStudyPlan(4, 10.0)}
                  className="bg-purple-600 text-white px-6 py-2 rounded-md hover:bg-purple-700 font-semibold"
                >
                  📅 Generate 4-Week Study Plan
                </button>
                <button
                  type="button"
                  onClick={() => generateStudyPlan(6, 10.0)}
                  className="bg-purple-500 text-white px-6 py-2 rounded-md hover:bg-purple-600 font-semibold"
                >
                  📅 Generate 6-Week Study Plan
                </button>
              </div>
            </div>
          )}

          {generatingPlan && (
            <div className="mt-6 p-4 bg-purple-50 text-purple-700 rounded-lg border border-purple-200">
              <p className="font-semibold">⏳ Generating personalized study plan...</p>
              <p className="text-sm mt-2">Creating weekly themes and daily tasks based on your skill gaps...</p>
            </div>
          )}

          {studyPlan && (
            <div className="mt-6 p-6 bg-white rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Your Study Plan</h2>
                <div className="text-sm text-gray-600">
                  {studyPlan.weeks} weeks • {studyPlan.hours_per_week}h/week • {studyPlan.total_estimated_hours?.toFixed(1) || 0}h total
                </div>
              </div>

              {/* Plan Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Weeks</p>
                  <p className="text-2xl font-bold text-blue-600">{studyPlan.weeks}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Total Hours</p>
                  <p className="text-2xl font-bold text-green-600">{studyPlan.total_estimated_hours?.toFixed(1) || 0}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Completion</p>
                  <p className="text-2xl font-bold text-purple-600">{studyPlan.completion_percentage?.toFixed(0) || 0}%</p>
                </div>
              </div>

              {/* Focus Areas */}
              {studyPlan.focus_areas && studyPlan.focus_areas.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Focus Areas</h3>
                  <div className="flex flex-wrap gap-2">
                    {studyPlan.focus_areas.map((area, idx) => (
                      <span key={idx} className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm">
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Weeks */}
              {studyPlan.weeks_data && studyPlan.weeks_data.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Weekly Breakdown</h3>
                  {studyPlan.weeks_data.map((week) => (
                    <div key={week.id} className="border-2 border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-bold text-lg text-gray-900">
                            Week {week.week_number}: {week.theme}
                          </h4>
                          {week.focus_skills && week.focus_skills.length > 0 && (
                            <p className="text-sm text-gray-600 mt-1">
                              Skills: {week.focus_skills.join(", ")}
                            </p>
                          )}
                        </div>
                        <p className="text-sm font-semibold text-gray-700">
                          {week.estimated_hours}h
                        </p>
                      </div>

                      {/* Days */}
                      {week.days && week.days.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {week.days.map((day) => (
                            <div key={day.id} className="bg-gray-50 rounded p-3">
                              <div className="flex justify-between items-center mb-2">
                                <div>
                                  <p className="font-semibold text-sm">
                                    Day {day.day_number} {day.date && `(${new Date(day.date).toLocaleDateString()})`}
                                  </p>
                                  {day.theme && (
                                    <p className="text-xs text-gray-600">{day.theme}</p>
                                  )}
                                </div>
                                <p className="text-xs text-gray-600">{day.estimated_hours}h</p>
                              </div>

                              {/* Tasks */}
                              {day.tasks && day.tasks.length > 0 && (
                                <div className="mt-2 space-y-1">
                                  {day.tasks.map((task) => (
                                    <div key={task.id} className="bg-white rounded p-2 text-xs">
                                      <div className="flex items-center gap-2">
                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                          task.task_type === 'learn' ? 'bg-blue-100 text-blue-800' :
                                          task.task_type === 'practice' ? 'bg-green-100 text-green-800' :
                                          'bg-yellow-100 text-yellow-800'
                                        }`}>
                                          {task.task_type}
                                        </span>
                                        <span className="font-semibold">{task.title}</span>
                                        <span className="text-gray-500 ml-auto">{task.estimated_minutes}min</span>
                                      </div>
                                      {task.description && (
                                        <p className="text-gray-600 mt-1 ml-12">{task.description}</p>
                                      )}
                                      {task.skill_names && task.skill_names.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-1 ml-12">
                                          {task.skill_names.map((skill, idx) => (
                                            <span key={idx} className="bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded text-xs">
                                              {skill}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default Upload




