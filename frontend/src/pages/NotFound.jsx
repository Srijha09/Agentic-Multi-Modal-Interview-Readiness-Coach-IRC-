import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <div className="px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Page not found</h1>
        <p className="text-gray-600 mb-6">
          The page you are looking for does not exist.
        </p>
        <Link
          to="/"
          className="inline-block bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
        >
          Back to Home
        </Link>
      </div>
    </div>
  )
}

export default NotFound

