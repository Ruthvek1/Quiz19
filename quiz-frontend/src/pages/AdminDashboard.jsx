import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import LoadingSpinner from '../components/LoadingSpinner'
import { 
  BarChart3, 
  Users, 
  BookOpen, 
  TrendingUp, 
  Clock,
  Award,
  Activity,
  Plus,
  Eye,
  Settings
} from 'lucide-react'

function AdminDashboard() {
  const { apiCall } = useAuth()
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalQuizzes: 0,
    totalSessions: 0,
    averageScore: 0,
    activeUsers: 0,
    recentActivity: []
  })
  const [recentQuizzes, setRecentQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load dashboard statistics
      const [statsResponse, quizzesResponse] = await Promise.all([
        apiCall('/admin/stats'),
        apiCall('/quizzes')
      ])
      
      if (statsResponse.success) {
        setStats(statsResponse.data)
      }
      
      if (quizzesResponse.success) {
        setRecentQuizzes(quizzesResponse.data.slice(0, 5)) // Show last 5 quizzes
      }
      
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <LoadingSpinner text="Loading admin dashboard..." />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage your quiz platform and monitor activity</p>
        </div>
        <div className="flex space-x-3">
          <Button asChild>
            <Link to="/admin/quizzes">
              <Plus className="w-4 h-4 mr-2" />
              Create Quiz
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/admin/users">
              <Users className="w-4 h-4 mr-2" />
              Manage Users
            </Link>
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Users</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalUsers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <BookOpen className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Quizzes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalQuizzes}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Quiz Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalSessions}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Award className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.averageScore ? `${stats.averageScore}%` : '--'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Quizzes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BookOpen className="w-5 h-5 mr-2" />
              Recent Quizzes
            </CardTitle>
            <CardDescription>
              Latest quizzes created on the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentQuizzes.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No quizzes created yet</p>
                <Button asChild>
                  <Link to="/admin/quizzes">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Quiz
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentQuizzes.map((quiz) => (
                  <div key={quiz.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{quiz.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {quiz.total_questions} questions • {quiz.duration_minutes} minutes
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Created {formatDate(quiz.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        quiz.is_active 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {quiz.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <Button variant="ghost" size="sm" asChild>
                        <Link to={`/admin/quizzes/${quiz.id}`}>
                          <Eye className="w-4 h-4" />
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))}
                <div className="text-center pt-4">
                  <Button variant="outline" asChild>
                    <Link to="/admin/quizzes">View All Quizzes</Link>
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              System Status
            </CardTitle>
            <CardDescription>
              Current platform activity and health
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                  <span className="font-medium text-green-900">System Status</span>
                </div>
                <span className="text-green-700 font-medium">Online</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <Users className="w-5 h-5 text-blue-600 mr-3" />
                  <span className="font-medium text-blue-900">Active Users</span>
                </div>
                <span className="text-blue-700 font-medium">{stats.activeUsers}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center">
                  <Clock className="w-5 h-5 text-purple-600 mr-3" />
                  <span className="font-medium text-purple-900">Server Uptime</span>
                </div>
                <span className="text-purple-700 font-medium">99.9%</span>
              </div>

              <div className="pt-4">
                <Button variant="outline" className="w-full">
                  <Settings className="w-4 h-4 mr-2" />
                  System Settings
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common administrative tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button asChild className="h-auto p-6 flex-col">
              <Link to="/admin/quizzes">
                <BookOpen className="w-8 h-8 mb-2" />
                <span className="font-medium">Manage Quizzes</span>
                <span className="text-sm opacity-75">Create, edit, and organize quizzes</span>
              </Link>
            </Button>

            <Button asChild variant="outline" className="h-auto p-6 flex-col">
              <Link to="/admin/users">
                <Users className="w-8 h-8 mb-2" />
                <span className="font-medium">User Management</span>
                <span className="text-sm opacity-75">View and manage user accounts</span>
              </Link>
            </Button>

            <Button asChild variant="outline" className="h-auto p-6 flex-col">
              <Link to="/admin/analytics">
                <BarChart3 className="w-8 h-8 mb-2" />
                <span className="font-medium">Analytics</span>
                <span className="text-sm opacity-75">View detailed reports and insights</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AdminDashboard

