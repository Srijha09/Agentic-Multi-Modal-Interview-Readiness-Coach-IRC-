import { Link } from 'react-router-dom'
import { useState } from 'react'

import api from '../api/client.js'

function Upload() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [userId, setUserId] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [statusLabel, setStatusLabel] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)

  const uploadDocument = async ({ file, documentType, userIdValue }) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    formData.append('user_id', String(userIdValue))

    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    return response.data
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    setResults(null)
    setStatusLabel('')

    if (!resumeFile) {
      setError('Please upload a resume file.')
      return
    }

    setIsSubmitting(true)
    setStatusLabel('Uploading resume…')

    try {
      const resumeResponse = await uploadDocument({
        file: resumeFile,
        documentType: 'resume',
        userIdValue: userId,
      })

      let jobResponse = null
      const trimmedJob = jobDescription.trim()
      if (trimmedJob) {
        setStatusLabel('Uploading job description…')
        const jobFile = new File([trimmedJob], 'job_description.txt', {
          type: 'text/plain',
        })
        jobResponse = await uploadDocument({
          file: jobFile,
          documentType: 'job_description',
          userIdValue: userId,
        })
      }

      const resumeId = resumeResponse?.id ?? resumeResponse?.document_id
      const jobId = jobResponse?.id ?? jobResponse?.document_id

      const statusParts = [`Resume uploaded (ID: ${resumeId}).`]
      if (jobResponse) {
        statusParts.push(`Job description uploaded (ID: ${jobId}).`)
      }

      setResults({
        resume: resumeResponse,
        jobDescription: jobResponse,
      })
      setMessage(statusParts.join(' '))

      if (jobId) {
        setStatusLabel(
          'Running LangGraph onboarding (gap analysis + study plan). This usually takes 3–6 minutes…',
        )
        const onboarding = await api.post('/api/v1/graph/onboarding', null, {
          params: {
            user_id: userId,
            resume_document_id: resumeId,
            jd_document_id: jobId,
            weeks: 4,
            hours_per_week: 10,
            generate_plan: true,
          },
        })
        const planId = onboarding.data?.study_plan_id
        const gapCount = onboarding.data?.gap_count ?? 0
        setResults((prev) => ({ ...prev, onboarding }))
        setMessage(
          planId
            ? `Done! ${gapCount} skill gaps identified. Study plan #${planId} created.`
            : `Done! ${gapCount} skill gaps identified (plan generation skipped or failed).`,
        )
        setStatusLabel('')
      } else {
        setStatusLabel('')
        setMessage((prev) =>
          `${prev} Add a job description to run gap analysis and planning.`,
        )
      }
    } catch (submitError) {
      const detail = submitError?.response?.data?.detail
      const isTimeout = submitError?.code === 'ECONNABORTED'
      setError(
        isTimeout
          ? 'Request timed out. The backend may still be working—check the terminal, then refresh or try again.'
          : detail || submitError?.message || 'Upload failed. Please try again.',
      )
      setStatusLabel('')
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

