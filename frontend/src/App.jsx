import React, { useEffect, useState } from 'react'
import { getMentorSummary, logout } from './api'
import Login from './Login'
import MentorWeek from './MentorWeek'
import AdminPlans from './AdminPlans'

function MentorSummaryView() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMentorSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="workstation-tile" style={{ textAlign: 'left' }}>
        <div className="micro-label"><span className="micro-label-icon"></span>Loading Intelligence</div>
        <p className="panel-subtitle">Compiling career mastery telemetry...</p>
      </div>
    )
  }

  // Fallback demo summary if API is starting or empty
  const focus = summary?.weekly_focus || 'Deep Dive into Distributed Systems Architecture & Async Message Queues'
  const gaps = summary?.top_gaps || [
    'Advanced MongoDB Indexing Strategy & Sharding',
    'FastAPI Async Middleware & Custom Dependency Injection',
    'Distributed Tracing & Telemetry (OpenTelemetry)'
  ]
  const steps = summary?.next_steps || [
    'Implement Redis caching layer for career assessment endpoints',
    'Write E2E Playwright validation tests for authentication flow',
    'Configure Production Docker Compose with health checks'
  ]

  return (
    <div className="workstation-grid">
      {/* Sidebar Metrics */}
      <div className="sidebar-panel">
        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Verification Status</div>
          <div style={{ fontSize: 24, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)', marginBottom: 4, textAlign: 'left' }}>
            88.5%
          </div>
          <div className="panel-subtitle" style={{ fontSize: 12 }}>Overall Skill Verification Score</div>
          <div className="progress-container" style={{ marginTop: 12, marginBottom: 16 }}>
            <div className="progress-fill" style={{ width: '88.5%' }}></div>
          </div>
          <div className="metric-row">
            <span className="metric-name">Verified Skills</span>
            <span className="metric-value">14 / 16</span>
          </div>
          <div className="metric-row">
            <span className="metric-name">Engine Level</span>
            <span className="metric-value">PROVE v0.1</span>
          </div>
        </div>

        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Current Focus Area</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginTop: 8, textAlign: 'left', lineHeight: 1.4 }}>
            {focus}
          </div>
        </div>
      </div>

      {/* Main Workstation Canvas */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* Top Skill Gaps Panel */}
        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Identified Growth Areas</div>
          <div className="panel-header">
            <h2 className="panel-title">Top Priority Skill Gaps</h2>
            <p className="panel-subtitle">Targeted competencies required for high-velocity promotion</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {gaps.map((gap, i) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    fontWeight: 700,
                    color: 'var(--accent-blue)',
                    background: '#eff6ff',
                    padding: '2px 8px',
                    borderRadius: 4
                  }}>
                    GAP-0{i + 1}
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {gap}
                  </span>
                </div>
                <span className="badge badge-amber">HIGH PRIORITY</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actionable Next Steps */}
        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Execution Pipeline</div>
          <div className="panel-header">
            <h2 className="panel-title">Actionable Next Steps</h2>
            <p className="panel-subtitle">Recommended immediate engineering actions</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {steps.map((step, i) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '12px 16px',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)'
              }}>
                <div style={{
                  width: 24,
                  height: 24,
                  borderRadius: 4,
                  background: 'var(--text-primary)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  fontWeight: 700
                }}>
                  {i + 1}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', flex: 1, textAlign: 'left' }}>
                  {step}
                </span>
                <span className="badge badge-emerald">READY</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [authed, setAuthed] = useState(Boolean(localStorage.getItem('prove_token')))
  const [view, setView] = useState('summary')

  const onLogin = () => setAuthed(true)
  const onLogout = () => { logout(); setAuthed(false) }

  return (
    <div className="app-container">
      {/* Top Workstation Header */}
      <header className="workstation-header">
        <div className="brand-section">
          <div className="brand-logo">PR</div>
          <div className="brand-text-container">
            <span className="brand-title">PROVE WORKSTATION</span>
            <span className="brand-subtitle">AI CAREER MASTERY & SKILL INFRASTRUCTURE</span>
          </div>
        </div>

        <div className="system-telemetry">
          <div className="telemetry-chip">
            <span className="status-dot"></span>
            SYSTEM: ONLINE
          </div>
          <div className="telemetry-chip">
            LATENCY: 14ms
          </div>
        </div>
      </header>

      {authed ? (
        <>
          {/* Asymmetrical Navigation Rail */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 28,
            padding: '8px 12px',
            background: 'var(--bg-surface)',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)'
          }}>
            <nav className="nav-rail">
              <button
                className={`nav-button ${view === 'summary' ? 'active' : ''}`}
                onClick={() => setView('summary')}
              >
                📊 Dashboard Summary
              </button>
              <button
                className={`nav-button ${view === 'week' ? 'active' : ''}`}
                onClick={() => setView('week')}
              >
                ⚡ 7-Day Sprint Plan
              </button>
              <button
                className={`nav-button ${view === 'admin' ? 'active' : ''}`}
                onClick={() => setView('admin')}
              >
                🛡 Admin Registry
              </button>
            </nav>

            <button className="nav-button nav-button-logout" onClick={onLogout}>
              Logout
            </button>
          </div>

          {/* Active Workstation Canvas View */}
          <main>
            {view === 'week' ? (
              <MentorWeek />
            ) : view === 'admin' ? (
              <AdminPlans />
            ) : (
              <MentorSummaryView />
            )}
          </main>
        </>
      ) : (
        <Login onLogin={onLogin} />
      )}
    </div>
  )
}
