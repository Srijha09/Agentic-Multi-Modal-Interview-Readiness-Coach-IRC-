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
        </form>
      </div>
    </div>
  )
}

export default Upload




