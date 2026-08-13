import React, { useEffect, useState } from 'react'
import { getWeeklyPlan, saveWeeklyPlan, deleteWeeklyPlan, completeMilestone } from './api'

export default function MentorWeek() {
  const [plan, setPlan] = useState(null)
  const [editing, setEditing] = useState(false)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const p = await getWeeklyPlan()
      setPlan(p)
    } catch (err) {
      setPlan(null)
    } finally {
      setLoading(false)
    }
  }

  function makeEmpty() {
    return {
      title: '7-Day Career Mastery Sprint',
      milestones: Array.from({ length: 7 }).map((_, i) => ({
        day: i,
        text: `Day ${i + 1}: ${
          ['System Architecture Assessment', 'Database Optimization & Indexing', 'API Security & Auth Controls', 'Async Event Architecture', 'Performance Profiling & Caching', 'E2E Testing & Verification', 'Production Deployment Readiness'][i]
        }`,
        created_at: new Date().toISOString(),
        completed_at: null,
        progress: 0
      }))
    }
  }

  async function handleSave() {
    setStatus('Saving sprint plan...')
    try {
      const p = plan || makeEmpty()
      await saveWeeklyPlan(p)
      setStatus('Sprint plan saved successfully')
      setEditing(false)
      await load()
    } catch (err) {
      setStatus('Error saving plan')
    }
  }

  async function handleDelete() {
    if (!confirm('Are you sure you want to delete this weekly sprint plan?')) return
    await deleteWeeklyPlan()
    setPlan(null)
  }

  async function handleComplete(idx) {
    setStatus('Updating milestone...')
    try {
      await completeMilestone(idx)
      setStatus('Milestone marked complete!')
      await load()
    } catch (err) {
      setStatus('Error updating milestone')
    }
  }

  function updateMilestone(idx, patch) {
    setPlan(prev => {
      if (!prev) return prev
      const milestones = prev.milestones.map((m, i) => i === idx ? { ...m, ...patch } : m)
      return { ...prev, milestones }
    })
  }

  if (loading) {
    return (
      <div className="workstation-tile" style={{ textAlign: 'left' }}>
        <div className="micro-label"><span className="micro-label-icon"></span>Loading Telemetry</div>
        <p className="panel-subtitle">Fetching weekly engineering sprint data...</p>
      </div>
    )
  }

  const completedCount = plan?.milestones?.filter(m => m.completed_at || m.progress === 100)?.length || 0
  const totalCount = plan?.milestones?.length || 7
  const overallPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  if (!plan) {
    return (
      <div className="workstation-tile" style={{ textAlign: 'left' }}>
        <div className="micro-label"><span className="micro-label-icon"></span>Weekly Sprint Framework</div>
        <div className="panel-header">
          <h2 className="panel-title">No Active Sprint Plan</h2>
          <p className="panel-subtitle">Initialize a structured 7-day engineering mastery sprint</p>
        </div>
        <button className="btn-primary" onClick={() => { setPlan(makeEmpty()); setEditing(true) }}>
          + Initialize 7-Day Sprint
        </button>
      </div>
    )
  }

  return (
    <div className="workstation-grid">
      {/* Left Sidebar Telemetry */}
      <div className="sidebar-panel">
        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Sprint Progress</div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginBottom: 8, textAlign: 'left' }}>
            {overallPercentage}%
          </div>
          <div className="panel-subtitle" style={{ fontSize: 12 }}>Sprint Completion Index</div>
          <div className="progress-container" style={{ marginBottom: 16 }}>
            <div className="progress-fill" style={{ width: `${overallPercentage}%` }}></div>
          </div>
          <div className="metric-row">
            <span className="metric-name">Completed Tasks</span>
            <span className="metric-value">{completedCount} / {totalCount}</span>
          </div>
          <div className="metric-row">
            <span className="metric-name">Status</span>
            <span className="badge badge-emerald">ACTIVE</span>
          </div>
        </div>

        <div className="workstation-tile">
          <div className="micro-label"><span className="micro-label-icon"></span>Actions</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {editing ? (
              <button className="btn-primary" onClick={handleSave} style={{ width: '100%' }}>
                Save Sprint Changes
              </button>
            ) : (
              <button className="btn-secondary" onClick={() => setEditing(true)} style={{ width: '100%' }}>
                Edit Sprint Milestones
              </button>
            )}
            <button className="btn-danger" onClick={handleDelete} style={{ width: '100%' }}>
              Delete Sprint
            </button>
          </div>
          {status && (
            <div style={{ marginTop: 12, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)', textAlign: 'left' }}>
              ℹ {status}
            </div>
          )}
        </div>
      </div>

      {/* Main Canvas: Density Wave Sprint Cards */}
      <div>
        <div className="workstation-tile" style={{ marginBottom: 24 }}>
          <div className="micro-label"><span className="micro-label-icon"></span>Engineering Mastery Roadmap</div>
          <div className="panel-header" style={{ marginBottom: 0 }}>
            <h2 className="panel-title">{plan.title || 'Weekly Sprint Plan'}</h2>
            <p className="panel-subtitle">7-Day structured milestone execution framework</p>
          </div>
        </div>

        <div>
          {plan.milestones.map((m, idx) => {
            const isDone = Boolean(m.completed_at || m.progress === 100)
            return (
              <div key={idx} className={`sprint-card ${isDone ? 'completed' : ''}`}>
                <div className="sprint-header">
                  <span className="day-badge">DAY 0{idx + 1}</span>
                  <span className={`badge ${isDone ? 'badge-emerald' : 'badge-blue'}`}>
                    {isDone ? '✓ COMPLETED' : 'IN PROGRESS'}
                  </span>
                </div>

                {editing ? (
                  <div style={{ marginTop: 12 }}>
                    <input
                      className="form-input"
                      style={{ marginBottom: 12 }}
                      value={m.text}
                      onChange={e => updateMilestone(idx, { text: e.target.value })}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span className="form-label">Progress:</span>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        className="form-input"
                        style={{ width: 90 }}
                        value={m.progress}
                        onChange={e => {
                          const v = Number(e.target.value) || 0
                          updateMilestone(idx, { progress: Math.max(0, Math.min(100, v)) })
                        }}
                      />
                      <span style={{ fontSize: 13, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>%</span>
                    </div>
                  </div>
                ) : (
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, textAlign: 'left' }}>
                      {m.text}
                    </h3>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, marginRight: 24 }}>
                        <div className="progress-container" style={{ margin: 0 }}>
                          <div className="progress-fill" style={{ width: `${m.progress}%` }}></div>
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>
                          {m.progress}%
                        </span>
                      </div>
                      <button
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: 12 }}
                        onClick={() => handleComplete(idx)}
                      >
                        {isDone ? 'Reopen' : 'Mark Complete'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
