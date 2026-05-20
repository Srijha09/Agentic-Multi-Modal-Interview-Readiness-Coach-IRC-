import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function Upload() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [userId, setUserId] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusLabel, setStatusLabel] = useState('')
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

  const handleSubmit = async (event) => {
    event.preventDefault()
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
      setIsSubmitting(false)
    }
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Upload Documents</h1>
        <p className="text-gray-600 mb-6">
          Upload your resume and paste a job description to generate a personalized plan.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resume (PDF or DOCX)
            </label>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Description
            </label>
            <textarea
              rows="8"
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the job description here..."
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              User ID
            </label>
            <input
              type="number"
              min="1"
              value={userId}
              onChange={(event) => setUserId(Number(event.target.value) || 1)}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-primary-600 text-white px-4 py-3 rounded hover:bg-primary-700 disabled:opacity-60"
          >
            {isSubmitting
              ? statusLabel || 'Working…'
              : 'Upload & Analyze'}
          </button>
        </form>

        {isSubmitting && statusLabel ? (
          <div
            className="mt-4 rounded bg-blue-50 text-blue-800 px-4 py-3 text-sm"
            role="status"
          >
            {statusLabel}
          </div>
        ) : null}

        {message ? (
          <div className="mt-6 rounded bg-green-50 text-green-700 px-4 py-3">
            ✓ {message}
          </div>
        ) : null}

        {error ? (
          <div className="mt-6 rounded bg-red-50 text-red-700 px-4 py-3">
            {error}
          </div>
        ) : null}

        {results ? (
          <div className="mt-6 rounded bg-gray-50 px-4 py-4">
            <h2 className="text-lg font-semibold mb-2">Upload Results</h2>
            <div className="text-sm text-gray-600">
              Resume ID: {results.resume?.id ?? results.resume?.document_id ?? 'N/A'}
            </div>
            {results.jobDescription ? (
              <div className="text-sm text-gray-600">
                Job Description ID: {results.jobDescription?.id ?? results.jobDescription?.document_id ?? 'N/A'}
              </div>
            ) : null}
            {results.onboarding ? (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-800 mb-1">Onboarding</h3>
                <div className="text-sm text-gray-600">
                  Skill gaps: {results.onboarding.gap_count ?? '—'}
                </div>
                {results.onboarding.study_plan_id ? (
                  <div className="text-sm text-gray-600">
                    Study plan ID: {results.onboarding.study_plan_id}
                  </div>
                ) : null}
                {results.onboarding.messages?.length ? (
                  <ul className="mt-2 text-xs text-gray-500 list-disc pl-4">
                    {results.onboarding.messages.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="mt-6">
          <Link
            to="/"
            className="inline-block text-primary-700 hover:text-primary-800"
          >
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Upload

