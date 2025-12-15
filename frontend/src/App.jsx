import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { authApi } from './api/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import Groups from './pages/Groups'
import Posts from './pages/Posts'
import Proxies from './pages/Proxies'

function PrivateRoute({ children }) {
  if (!authApi.isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return children
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout>
                <Navigate to="/dashboard" replace />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/accounts"
          element={
            <PrivateRoute>
              <Layout>
                <Accounts />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/groups"
          element={
            <PrivateRoute>
              <Layout>
                <Groups />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/posts"
          element={
            <PrivateRoute>
              <Layout>
                <Posts />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/proxies"
          element={
            <PrivateRoute>
              <Layout>
                <Proxies />
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App

