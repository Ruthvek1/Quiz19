import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { useAuth } from './useAuth'

const SOCKET_URL = 'http://localhost:5001'

export function useSocket() {
  const { token } = useAuth()
  const socketRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!token) {
      return
    }

    // Initialize socket connection
    socketRef.current = io(SOCKET_URL, {
      auth: {
        token: token
      },
      transports: ['websocket', 'polling']
    })

    const socket = socketRef.current

    // Connection event handlers
    socket.on('connect', () => {
      console.log('Connected to server')
      setIsConnected(true)
      setError(null)
    })

    socket.on('disconnect', () => {
      console.log('Disconnected from server')
      setIsConnected(false)
    })

    socket.on('connect_error', (err) => {
      console.error('Connection error:', err)
      setError(err.message)
      setIsConnected(false)
    })

    socket.on('error', (err) => {
      console.error('Socket error:', err)
      setError(err.message)
    })

    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.disconnect()
      }
    }
  }, [token])

  const emit = (event, data) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit(event, data)
    }
  }

  const on = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback)
    }
  }

  const off = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.off(event, callback)
    }
  }

  return {
    socket: socketRef.current,
    isConnected,
    error,
    emit,
    on,
    off
  }
}

export function useQuizSocket(sessionToken) {
  const { socket, isConnected, error, emit, on, off } = useSocket()
  const [quizState, setQuizState] = useState({
    timeRemaining: null,
    currentQuestionIndex: 0,
    totalQuestions: 0,
    isJoined: false
  })
  const [activeUsers, setActiveUsers] = useState(0)

  useEffect(() => {
    if (!socket || !isConnected || !sessionToken) {
      return
    }

    // Join quiz session
    emit('join_quiz', { session_token: sessionToken })

    // Quiz event handlers
    const handleQuizJoined = (data) => {
      console.log('Joined quiz:', data)
      setQuizState(prev => ({
        ...prev,
        timeRemaining: data.time_remaining,
        currentQuestionIndex: data.current_question_index,
        totalQuestions: data.total_questions,
        isJoined: true
      }))
    }

    const handleTimeSync = (data) => {
      setQuizState(prev => ({
        ...prev,
        timeRemaining: data.time_remaining
      }))
    }

    const handleQuestionChanged = (data) => {
      setQuizState(prev => ({
        ...prev,
        currentQuestionIndex: data.question_index
      }))
    }

    const handleAnswerSubmitted = (data) => {
      console.log('Answer submitted:', data)
    }

    const handleQuizCompleted = (data) => {
      console.log('Quiz completed:', data)
      setQuizState(prev => ({
        ...prev,
        isJoined: false
      }))
    }

    const handleUserJoined = (data) => {
      console.log('User joined:', data)
      setActiveUsers(prev => prev + 1)
    }

    const handleUserLeft = (data) => {
      console.log('User left:', data)
      setActiveUsers(prev => Math.max(0, prev - 1))
    }

    // Register event listeners
    on('quiz_joined', handleQuizJoined)
    on('time_sync', handleTimeSync)
    on('question_changed', handleQuestionChanged)
    on('answer_submitted', handleAnswerSubmitted)
    on('quiz_completed', handleQuizCompleted)
    on('user_joined', handleUserJoined)
    on('user_left', handleUserLeft)

    // Cleanup
    return () => {
      off('quiz_joined', handleQuizJoined)
      off('time_sync', handleTimeSync)
      off('question_changed', handleQuestionChanged)
      off('answer_submitted', handleAnswerSubmitted)
      off('quiz_completed', handleQuizCompleted)
      off('user_joined', handleUserJoined)
      off('user_left', handleUserLeft)
      
      if (quizState.isJoined) {
        emit('leave_quiz')
      }
    }
  }, [socket, isConnected, sessionToken])

  // Auto time sync every 30 seconds
  useEffect(() => {
    if (!socket || !isConnected || !quizState.isJoined) {
      return
    }

    const interval = setInterval(() => {
      emit('request_time_sync')
    }, 30000)

    return () => clearInterval(interval)
  }, [socket, isConnected, quizState.isJoined])

  const submitAnswer = (questionId, selectedAnswer, timeTaken) => {
    emit('submit_answer', {
      question_id: questionId,
      selected_answer: selectedAnswer,
      time_taken: timeTaken
    })
  }

  const nextQuestion = (questionIndex) => {
    emit('next_question', { question_index: questionIndex })
  }

  const finishQuiz = () => {
    emit('finish_quiz')
  }

  const requestTimeSync = () => {
    emit('request_time_sync')
  }

  return {
    isConnected,
    error,
    quizState,
    activeUsers,
    submitAnswer,
    nextQuestion,
    finishQuiz,
    requestTimeSync
  }
}

export default useSocket

