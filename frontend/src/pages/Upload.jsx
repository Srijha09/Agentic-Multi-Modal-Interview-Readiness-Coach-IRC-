import { useState } from 'react'
import axios from 'axios'

function Upload() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [uploadResult, setUploadResult] = useState(null)
  
  // For testing - use the user_id from create_test_user.py (typically 1)
  const TEST_USER_ID = 1

  const handleResumeChange = (e) => {
    setResumeFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setUploading(true)
    setMessage('')
    setUploadResult(null)

    try {
      // Upload resume if provided
      if (resumeFile) {
        const formData = new FormData()
        formData.append('file', resumeFile)
        formData.append('document_type', 'resume')
        formData.append('user_id', TEST_USER_ID.toString())

        const response = await axios.post('/api/v1/documents/upload', formData)
        
        setUploadResult({
          type: 'resume',
          data: response.data
        })
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
        </form>
      </div>
    </div>
  )
}

export default Upload




