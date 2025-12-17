import { Link } from 'react-router-dom'

function Home() {
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




