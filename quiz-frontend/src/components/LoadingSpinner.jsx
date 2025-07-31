import React from 'react'
import { Loader2 } from 'lucide-react'

function LoadingSpinner({ size = 'default', text = 'Loading...' }) {
  const sizeClasses = {
    small: 'h-4 w-4',
    default: 'h-8 w-8',
    large: 'h-12 w-12'
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] space-y-4">
      <Loader2 className={`animate-spin text-blue-600 ${sizeClasses[size]}`} />
      {text && (
        <p className="text-gray-600 text-sm font-medium">{text}</p>
      )}
    </div>
  )
}

export default LoadingSpinner

