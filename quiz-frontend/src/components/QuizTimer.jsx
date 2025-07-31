import React, { useState, useEffect } from 'react'
import { Clock, AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

function QuizTimer({ 
  initialTimeRemaining, 
  onTimeUp, 
  onTimeSync,
  isConnected = true,
  className = "" 
}) {
  const [timeRemaining, setTimeRemaining] = useState(initialTimeRemaining || 0)
  const [isWarning, setIsWarning] = useState(false)
  const [isCritical, setIsCritical] = useState(false)

  // Update time remaining when prop changes (from server sync)
  useEffect(() => {
    if (initialTimeRemaining !== null && initialTimeRemaining !== undefined) {
      setTimeRemaining(initialTimeRemaining)
    }
  }, [initialTimeRemaining])

  // Local countdown timer
  useEffect(() => {
    if (timeRemaining <= 0) {
      if (onTimeUp) {
        onTimeUp()
      }
      return
    }

    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        const newTime = Math.max(0, prev - 1)
        
        // Check for warning and critical states
        if (newTime <= 60 && newTime > 30) {
          setIsWarning(true)
          setIsCritical(false)
        } else if (newTime <= 30) {
          setIsWarning(true)
          setIsCritical(true)
        } else {
          setIsWarning(false)
          setIsCritical(false)
        }

        // Call onTimeUp when time reaches 0
        if (newTime === 0 && onTimeUp) {
          onTimeUp()
        }

        return newTime
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [timeRemaining, onTimeUp])

  // Request time sync every 2 minutes
  useEffect(() => {
    if (!onTimeSync) return

    const syncInterval = setInterval(() => {
      onTimeSync()
    }, 120000) // 2 minutes

    return () => clearInterval(syncInterval)
  }, [onTimeSync])

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const getTimerColor = () => {
    if (isCritical) return 'text-red-600'
    if (isWarning) return 'text-yellow-600'
    return 'text-gray-700'
  }

  const getBackgroundColor = () => {
    if (isCritical) return 'bg-red-50 border-red-200'
    if (isWarning) return 'bg-yellow-50 border-yellow-200'
    return 'bg-white border-gray-200'
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Timer Display */}
      <div className={`flex items-center justify-center p-4 rounded-lg border-2 ${getBackgroundColor()}`}>
        <Clock className={`w-5 h-5 mr-2 ${getTimerColor()}`} />
        <span className={`text-2xl font-bold font-mono ${getTimerColor()}`}>
          {formatTime(timeRemaining)}
        </span>
        {!isConnected && (
          <div className="ml-2 w-2 h-2 bg-red-500 rounded-full animate-pulse" title="Disconnected" />
        )}
      </div>

      {/* Warning Messages */}
      {isCritical && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Less than 30 seconds remaining! Submit your answers now.
          </AlertDescription>
        </Alert>
      )}
      
      {isWarning && !isCritical && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            Less than 1 minute remaining. Please review your answers.
          </AlertDescription>
        </Alert>
      )}

      {/* Connection Status */}
      {!isConnected && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Connection lost. Timer may not be accurate. Reconnecting...
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default QuizTimer

