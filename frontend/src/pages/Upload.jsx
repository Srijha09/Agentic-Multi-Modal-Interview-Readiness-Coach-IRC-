import { useState } from 'react'
import axios from 'axios'

function Upload() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleResumeChange = (e) => {
    setResumeFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setUploading(true)
    setMessage('')

    try {
      const formData = new FormData()
      if (resumeFile) {
        formData.append('file', resumeFile)
        formData.append('document_type', 'resume')
      }

      // TODO: Implement actual API call
      // const response = await axios.post('/api/v1/documents/upload', formData)
      
      setMessage('Upload functionality will be implemented in Phase 2')
      setUploading(false)
    } catch (error) {
      setMessage('Error uploading file. Please try again.')
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
            <div className="mt-4 p-3 bg-blue-50 text-blue-700 rounded">
              {message}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default Upload




