import React, { useState } from 'react'
import { login } from './api'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      onLogin()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Authentication failed. Please check credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 440, margin: '40px auto 0 auto' }}>
      <div className="workstation-tile">
        <div className="micro-label">
          <span className="micro-label-icon"></span>
          Authentication Interface
        </div>

        <div className="panel-header" style={{ marginBottom: 24 }}>
          <h2 className="panel-title">Sign In to Workstation</h2>
          <p className="panel-subtitle">Access your PROVE technical career mastery dashboard</p>
        </div>

        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 6,
            background: '#fef2f2',
            border: '1px solid #fca5a5',
            color: '#b91c1c',
            fontSize: 13,
            marginBottom: 20,
            textAlign: 'left'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              className="form-input"
              placeholder="user@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: 28 }}>
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Authenticating...' : 'Sign In to PROVE'}
          </button>
        </form>

        <div style={{
          marginTop: 24,
          paddingTop: 16,
          borderTop: '1px dashed var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 11,
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)'
        }}>
          <span>ENV: CLOSED_BETA_V0.1</span>
          <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>● SECURE_AUTH</span>
        </div>
      </div>
    </div>
  )
}
