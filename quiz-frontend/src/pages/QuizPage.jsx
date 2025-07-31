import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useQuizSocket } from '../hooks/useSocket'
import SecurityWrapper from '../components/SecurityWrapper'
import QuizTimer from '../components/QuizTimer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import LoadingSpinner from '../components/LoadingSpinner'
import { 
  ChevronLeft, 
  ChevronRight, 
  Flag, 
  AlertTriangle,
  Eye,
  EyeOff,
  Shield
} from 'lucide-react'

function QuizPage() {
  const { sessionToken } = useParams()
  const navigate = useNavigate()
  const { apiCall } = useAuth()
  
  // Quiz state
  const [quiz, setQuiz] = useState(null)
  const [questions, setQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [questionStartTime, setQuestionStartTime] = useState(Date.now())
  
  // Security state
  const [securityEnabled, setSecurityEnabled] = useState(true)
  const [warningCount, setWarningCount] = useState(0)
  const [showSecurityWarning, setShowSecurityWarning] = useState(false)
  
  // WebSocket integration
  const {
    isConnected,
    error: socketError,
    quizState,
    submitAnswer,
    nextQuestion,
    finishQuiz,
    requestTimeSync
  } = useQuizSocket(sessionToken)

  useEffect(() => {
    loadQuizData()
  }, [sessionToken])

  useEffect(() => {
    // Reset question start time when question changes
    setQuestionStartTime(Date.now())
  }, [currentQuestionIndex])

  const loadQuizData = async () => {
    try {
      setLoading(true)
      
      // Load quiz session data
      const sessionResponse = await apiCall(`/sessions/${sessionToken}`)
      if (!sessionResponse.success) {
        setError('Invalid quiz session')
        return
      }

      const session = sessionResponse.data
      const quizResponse = await apiCall(`/quizzes/${session.quiz_id}`)
      if (!quizResponse.success) {
        setError('Failed to load quiz')
        return
      }

      setQuiz(quizResponse.data)
      setQuestions(quizResponse.data.questions || [])
      setCurrentQuestionIndex(session.current_question_index || 0)
      
    } catch (err) {
      setError('Failed to load quiz data')
      console.error('Quiz loading error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerSelect = (selectedAnswer) => {
    const questionId = questions[currentQuestionIndex]?.id
    if (!questionId) return

    const timeTaken = Math.floor((Date.now() - questionStartTime) / 1000)
    
    // Update local state
    setAnswers(prev => ({
      ...prev,
      [questionId]: selectedAnswer
    }))

    // Submit to server via WebSocket
    submitAnswer(questionId, selectedAnswer, timeTaken)
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      const newIndex = currentQuestionIndex + 1
      setCurrentQuestionIndex(newIndex)
      nextQuestion(newIndex)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      const newIndex = currentQuestionIndex - 1
      setCurrentQuestionIndex(newIndex)
      nextQuestion(newIndex)
    }
  }

  const handleFinishQuiz = async () => {
    if (isSubmitting) return

    try {
      setIsSubmitting(true)
      finishQuiz()
      navigate(`/results/${sessionToken}`)
    } catch (err) {
      setError('Failed to submit quiz')
      console.error('Quiz submission error:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTimeUp = () => {
    handleFinishQuiz()
  }

  const handleSecurityViolation = () => {
    setWarningCount(prev => prev + 1)
    setShowSecurityWarning(true)
    
    if (warningCount >= 2) {
      // Auto-submit quiz after 3 violations
      handleFinishQuiz()
    }
  }

  const currentQuestion = questions[currentQuestionIndex]
  const selectedAnswer = currentQuestion ? answers[currentQuestion.id] : null
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner text="Loading quiz..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Alert variant="destructive" className="max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <SecurityWrapper enabled={securityEnabled}>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{quiz?.title}</h1>
                <p className="text-sm text-gray-600">
                  Question {currentQuestionIndex + 1} of {questions.length}
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Security Status */}
                <div className="flex items-center space-x-2">
                  <Shield className={`w-4 h-4 ${securityEnabled ? 'text-green-600' : 'text-gray-400'}`} />
                  <span className="text-xs text-gray-600">
                    {securityEnabled ? 'Secure Mode' : 'Normal Mode'}
                  </span>
                </div>
                
                {/* Connection Status */}
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Security Warning */}
        {showSecurityWarning && (
          <Alert variant="destructive" className="max-w-4xl mx-auto mt-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Security violation detected! Warning {warningCount}/3. 
              {warningCount >= 2 && ' Quiz will be auto-submitted on next violation.'}
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content */}
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Timer Sidebar */}
            <div className="lg:col-span-1">
              <QuizTimer
                initialTimeRemaining={quizState.timeRemaining}
                onTimeUp={handleTimeUp}
                onTimeSync={requestTimeSync}
                isConnected={isConnected}
                className="sticky top-6"
              />
              
              {/* Question Navigation */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-sm">Question Navigation</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-5 gap-2">
                    {questions.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentQuestionIndex(index)}
                        className={`w-8 h-8 rounded text-xs font-medium transition-colors ${
                          index === currentQuestionIndex
                            ? 'bg-blue-600 text-white'
                            : answers[questions[index]?.id]
                            ? 'bg-green-100 text-green-700 border border-green-300'
                            : 'bg-gray-100 text-gray-600 border border-gray-300'
                        }`}
                      >
                        {index + 1}
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Question Content */}
            <div className="lg:col-span-3">
              {currentQuestion && (
                <Card>
                  <CardContent className="p-6">
                    {/* Question Image */}
                    {currentQuestion.question_image_path && (
                      <div className="mb-6">
                        <img
                          src={`http://localhost:5001${currentQuestion.question_image_path}`}
                          alt="Question"
                          className="w-full max-w-2xl mx-auto rounded-lg shadow-sm"
                          style={{ 
                            userSelect: 'none',
                            WebkitUserSelect: 'none',
                            pointerEvents: 'none'
                          }}
                        />
                      </div>
                    )}

                    {/* Fallback Text Question (if image not available) */}
                    {!currentQuestion.question_image_path && (
                      <div className="mb-6">
                        <h2 className="text-lg font-medium text-gray-900 mb-4">
                          {currentQuestion.question_text}
                        </h2>
                      </div>
                    )}

                    {/* Options Image */}
                    {currentQuestion.options_image_path && (
                      <div className="mb-6">
                        <img
                          src={`http://localhost:5001${currentQuestion.options_image_path}`}
                          alt="Answer Options"
                          className="w-full max-w-2xl mx-auto rounded-lg shadow-sm"
                          style={{ 
                            userSelect: 'none',
                            WebkitUserSelect: 'none',
                            pointerEvents: 'none'
                          }}
                        />
                      </div>
                    )}

                    {/* Answer Selection Buttons */}
                    <div className="grid grid-cols-2 gap-4">
                      {['a', 'b', 'c', 'd'].map((option) => (
                        <button
                          key={option}
                          onClick={() => handleAnswerSelect(option)}
                          className={`p-4 text-left rounded-lg border-2 transition-all ${
                            selectedAnswer === option
                              ? 'border-blue-600 bg-blue-50 text-blue-900'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <span className="font-medium text-lg">
                            {option.toUpperCase()}
                          </span>
                          {!currentQuestion.options_image_path && (
                            <span className="ml-3">
                              {currentQuestion.options[option]}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>

                    {/* Navigation Buttons */}
                    <div className="flex justify-between items-center mt-8">
                      <Button
                        variant="outline"
                        onClick={handlePreviousQuestion}
                        disabled={currentQuestionIndex === 0}
                      >
                        <ChevronLeft className="w-4 h-4 mr-2" />
                        Previous
                      </Button>

                      <div className="flex space-x-3">
                        {currentQuestionIndex === questions.length - 1 ? (
                          <Button
                            onClick={handleFinishQuiz}
                            disabled={isSubmitting}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Flag className="w-4 h-4 mr-2" />
                            {isSubmitting ? 'Submitting...' : 'Finish Quiz'}
                          </Button>
                        ) : (
                          <Button onClick={handleNextQuestion}>
                            Next
                            <ChevronRight className="w-4 h-4 ml-2" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>

        {/* Security Toggle (for testing - remove in production) */}
        <div className="fixed bottom-4 right-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSecurityEnabled(!securityEnabled)}
            className="opacity-50 hover:opacity-100"
          >
            {securityEnabled ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </SecurityWrapper>
  )
}

export default QuizPage

