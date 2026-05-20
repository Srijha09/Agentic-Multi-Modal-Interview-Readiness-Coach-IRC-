import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'

function Home() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('irc_openai_key') || '')
  const [status, setStatus] = useState('')

  useEffect(() => {
    if (status) {
      const timeout = setTimeout(() => setStatus(''), 2500)
      return () => clearTimeout(timeout)
    }
  }, [status])

  const handleSave = (event) => {
    event.preventDefault()
    const trimmed = apiKey.trim()
    if (!trimmed) {
      localStorage.removeItem('irc_openai_key')
      setApiKey('')
      setStatus('API key cleared.')
      return
    }
    localStorage.setItem('irc_openai_key', trimmed)
    setApiKey(trimmed)
    setStatus('API key saved locally.')
  }

  const handleClear = () => {
    localStorage.removeItem('irc_openai_key')
    setApiKey('')
    setStatus('API key cleared.')
  }

  return (
    <div className="px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Interview Readiness Coach
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          An intelligent, agentic interview preparation system that analyzes your resume
          and target job description to identify skill gaps, generate personalized study
          plans, and deliver daily practice sessions.
        </p>

        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-xl font-semibold mb-2">Connect your OpenAI API key</h2>
          <p className="text-gray-600 mb-4">
            Your key is stored locally in your browser and used only when you run tasks.
          </p>
          <form onSubmit={handleSave} className="space-y-3">
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="sk-..."
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
              >
                Save Key
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-100"
              >
                Clear Key
              </button>
            </div>
            {status ? (
              <p className="text-sm text-gray-500">{status}</p>
            ) : null}
          </form>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-2">Get Started</h2>
            <p className="text-gray-600 mb-4">
              Upload your resume and job description to begin your personalized
              interview preparation journey.
            </p>
            <Link
              to="/upload"
              className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Upload Documents
            </Link>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-2">Track Progress</h2>
            <p className="text-gray-600 mb-4">
              View your study plan, daily tasks, and track your mastery
              across different skills.
            </p>
            <Link
              to="/dashboard"
              className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home




