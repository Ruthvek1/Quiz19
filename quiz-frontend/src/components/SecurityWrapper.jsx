import React, { useEffect } from 'react'

function SecurityWrapper({ children, enabled = true }) {
  useEffect(() => {
    if (!enabled) return

    // Disable right-click context menu
    const handleContextMenu = (e) => {
      e.preventDefault()
      return false
    }

    // Disable text selection
    const handleSelectStart = (e) => {
      e.preventDefault()
      return false
    }

    // Disable drag and drop
    const handleDragStart = (e) => {
      e.preventDefault()
      return false
    }

    // Disable keyboard shortcuts for developer tools and copying
    const handleKeyDown = (e) => {
      // Disable F12 (Developer Tools)
      if (e.key === 'F12') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+Shift+I (Developer Tools)
      if (e.ctrlKey && e.shiftKey && e.key === 'I') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+Shift+J (Console)
      if (e.ctrlKey && e.shiftKey && e.key === 'J') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+U (View Source)
      if (e.ctrlKey && e.key === 'u') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+S (Save Page)
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+A (Select All)
      if (e.ctrlKey && e.key === 'a') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+C (Copy)
      if (e.ctrlKey && e.key === 'c') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+V (Paste)
      if (e.ctrlKey && e.key === 'v') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+X (Cut)
      if (e.ctrlKey && e.key === 'x') {
        e.preventDefault()
        return false
      }

      // Disable Ctrl+P (Print)
      if (e.ctrlKey && e.key === 'p') {
        e.preventDefault()
        return false
      }
    }

    // Disable print screen
    const handleKeyUp = (e) => {
      if (e.key === 'PrintScreen') {
        e.preventDefault()
        // Clear clipboard to prevent screenshot copying
        navigator.clipboard.writeText('')
        return false
      }
    }

    // Add event listeners
    document.addEventListener('contextmenu', handleContextMenu)
    document.addEventListener('selectstart', handleSelectStart)
    document.addEventListener('dragstart', handleDragStart)
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)

    // Add CSS to disable text selection
    const style = document.createElement('style')
    style.textContent = `
      .security-wrapper * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
        -webkit-touch-callout: none !important;
        -webkit-tap-highlight-color: transparent !important;
      }
      
      .security-wrapper img {
        -webkit-user-drag: none !important;
        -khtml-user-drag: none !important;
        -moz-user-drag: none !important;
        -o-user-drag: none !important;
        user-drag: none !important;
        pointer-events: none !important;
      }
    `
    document.head.appendChild(style)

    // Cleanup function
    return () => {
      document.removeEventListener('contextmenu', handleContextMenu)
      document.removeEventListener('selectstart', handleSelectStart)
      document.removeEventListener('dragstart', handleDragStart)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
      document.head.removeChild(style)
    }
  }, [enabled])

  // Add blur detection to detect when user switches tabs/windows
  useEffect(() => {
    if (!enabled) return

    let blurCount = 0
    const maxBlurCount = 3

    const handleBlur = () => {
      blurCount++
      console.warn(`Tab switch detected (${blurCount}/${maxBlurCount})`)
      
      if (blurCount >= maxBlurCount) {
        // Could trigger quiz submission or warning
        console.error('Maximum tab switches exceeded')
        // You could emit an event here to handle this in the parent component
      }
    }

    const handleFocus = () => {
      console.log('Tab focus regained')
    }

    window.addEventListener('blur', handleBlur)
    window.addEventListener('focus', handleFocus)

    return () => {
      window.removeEventListener('blur', handleBlur)
      window.removeEventListener('focus', handleFocus)
    }
  }, [enabled])

  if (!enabled) {
    return <>{children}</>
  }

  return (
    <div className="security-wrapper">
      {children}
      
      {/* Anti-cheating overlay for additional protection */}
      <div 
        className="fixed inset-0 pointer-events-none z-50"
        style={{
          background: 'transparent',
          userSelect: 'none',
          WebkitUserSelect: 'none',
          MozUserSelect: 'none',
          msUserSelect: 'none'
        }}
      />
    </div>
  )
}

export default SecurityWrapper

