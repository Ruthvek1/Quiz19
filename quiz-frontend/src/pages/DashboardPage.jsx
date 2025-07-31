import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import LoadingSpinner from '../components/LoadingSpinner'
import { 
  BookOpen, 
  Clock, 
  Users, 
  Trophy, 
  Play, 
  Calendar,
  Target,
  TrendingUp
} from 'lucide-react'

function DashboardPage() {
  const { user, apiCall } = useAuth()
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadQuizzes()
  }, [])

  const loadQuizzes = async () => {
    try {
      setLoading(true)
      const response = await apiCall('/quizzes')
      setQuizzes(response.data)
    } catch (err) {
      setError('Failed to load quizzes. Please try again.')
      console.error('Error loading quizzes:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'No time limit'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getQuizStatus = (quiz) => {
    if (!quiz.is_available) {
      return { status: 'unavailable', color: 'bg-gray-500', text: 'Unavailable' }
    }
    
    const now = new Date()
    const startTime = quiz.start_time ? new Date(quiz.start_time) : null
    const endTime = quiz.end_time ? new Date(quiz.end_time) : null
    
    if (startTime && now < startTime) {
      return { status: 'upcoming', color: 'bg-yellow-500', text: 'Upcoming' }
    }
    
    if (endTime && now > endTime) {
      return { status: 'expired', color: 'bg-red-500', text: 'Expired' }
    }
    
    return { status: 'available', color: 'bg-green-500', text: 'Available' }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <LoadingSpinner text="Loading your dashboard..." />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.username}!
        </h1>
        <p className="text-gray-600">
          Ready to test your knowledge? Choose from the available quizzes below.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Available Quizzes</p>
                <p className="text-2xl font-bold text-gray-900">
                  {quizzes.filter(q => getQuizStatus(q).status === 'available').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Trophy className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Target className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">--</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Best Score</p>
                <p className="text-2xl font-bold text-gray-900">--</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Available Quizzes */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Available Quizzes</h2>
        
        {quizzes.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Quizzes Available</h3>
              <p className="text-gray-600">
                There are no quizzes available at the moment. Check back later!
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quizzes.map((quiz) => {
              const status = getQuizStatus(quiz)
              const isAvailable = status.status === 'available'
              
              return (
                <Card key={quiz.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2">{quiz.title}</CardTitle>
                        <Badge className={`${status.color} text-white`}>
                          {status.text}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <CardDescription className="mb-4 line-clamp-3">
                      {quiz.description || 'No description available.'}
                    </CardDescription>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="w-4 h-4 mr-2" />
                        <span>{quiz.duration_minutes} minutes</span>
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <BookOpen className="w-4 h-4 mr-2" />
                        <span>{quiz.total_questions} questions</span>
                      </div>
                      {quiz.start_time && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span>Starts: {formatDate(quiz.start_time)}</span>
                        </div>
                      )}
                      {quiz.end_time && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span>Ends: {formatDate(quiz.end_time)}</span>
                        </div>
                      )}
                    </div>
                    
                    <Button 
                      asChild 
                      className="w-full" 
                      disabled={!isAvailable}
                      variant={isAvailable ? "default" : "secondary"}
                    >
                      {isAvailable ? (
                        <Link to={`/quiz/${quiz.id}`}>
                          <Play className="w-4 h-4 mr-2" />
                          Start Quiz
                        </Link>
                      ) : (
                        <span>
                          {status.status === 'upcoming' ? 'Not Started' : 
                           status.status === 'expired' ? 'Expired' : 'Unavailable'}
                        </span>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* Recent Results Section */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Results</h2>
        <Card>
          <CardContent className="p-12 text-center">
            <Trophy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
            <p className="text-gray-600">
              Complete your first quiz to see your results here.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default DashboardPage

