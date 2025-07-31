import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { Toaster } from '@/components/ui/toaster'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import QuizPage from './pages/QuizPage'
import ResultPage from './pages/ResultPage'
import AdminDashboard from './pages/AdminDashboard'
import AdminQuizzes from './pages/AdminQuizzes'
import AdminUsers from './pages/AdminUsers'

// Components
import Navbar from './components/Navbar'
import LoadingSpinner from './components/LoadingSpinner'

import './App.css'

// Protected Route Component
function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <LoadingSpinner />
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

// Public Route Component (redirect if already logged in)
function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <LoadingSpinner />
  }
  
  if (user) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function AppContent() {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gray-50">
      {user && <Navbar />}
      <main className={user ? "pt-16" : ""}>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          } />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } />
          <Route path="/quiz/:quizId" element={
            <ProtectedRoute>
              <QuizPage />
            </ProtectedRoute>
          } />
          <Route path="/result/:sessionToken" element={
            <ProtectedRoute>
              <ResultPage />
            </ProtectedRoute>
          } />
          
          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          <Route path="/admin/quizzes" element={
            <ProtectedRoute adminOnly>
              <AdminQuizzes />
            </ProtectedRoute>
          } />
          <Route path="/admin/users" element={
            <ProtectedRoute adminOnly>
              <AdminUsers />
            </ProtectedRoute>
          } />
          
          {/* Default Route */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
      <Toaster />
    </div>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  )
}

export default App
