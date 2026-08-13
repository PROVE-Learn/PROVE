import React, { useEffect, useState } from 'react'
import { adminListWeeklyPlans, adminDeleteUserPlan } from './api'

export default function AdminPlans() {
  const [plans, setPlans] = useState(null)
  const [status, setStatus] = useState(null)

  useEffect(() => { load() }, [])

  async function load() {
    setStatus('Fetching telemetry...')
    try {
      const r = await adminListWeeklyPlans()
      setPlans(r || [])
      setStatus(null)
    } catch (err) {
      setStatus('Failed to load admin plans')
    }
  }

  async function handleDelete(userId) {
    if (!confirm(`Confirm deletion of weekly plan for user ID "${userId}"?`)) return
    setStatus(`Deleting plan for ${userId}...`)
    try {
      await adminDeleteUserPlan(userId)
      setStatus(`Plan for ${userId} deleted.`)
      await load()
    } catch (err) {
      setStatus('Error deleting plan')
    }
  }

  return (
    <div className="workstation-grid-full">
      <div className="workstation-tile">
        <div className="micro-label"><span className="micro-label-icon"></span>Administrative Telemetry Panel</div>
        
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 className="panel-title">System User Sprint Plans</h2>
            <p className="panel-subtitle">Manage active engineering roadmap instances across all accounts</p>
          </div>
          <button className="btn-secondary" onClick={load} style={{ fontSize: 12, padding: '6px 12px' }}>
            🔄 Refresh Registry
          </button>
        </div>

        {status && (
          <div style={{ marginBottom: 16, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)', textAlign: 'left' }}>
            ℹ Status: {status}
          </div>
        )}

        {!plans ? (
          <div style={{ padding: 24, color: 'var(--text-muted)', textAlign: 'left' }}>
            Loading plan data...
          </div>
        ) : plans.length === 0 ? (
          <div style={{ padding: 24, color: 'var(--text-muted)', textAlign: 'left' }}>
            No active user plans found in registry.
          </div>
        ) : (
          <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
            <table className="workstation-table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Sprint Plan Title</th>
                  <th>Total Milestones</th>
                  <th>Created Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((p, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {p.user_id || p.userId || `usr_${i + 101}`}
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {p.title || 'Weekly Sprint Plan'}
                    </td>
                    <td>
                      <span className="badge badge-blue">
                        {p.milestones?.length || 0} Milestones
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td>
                      <button
                        className="btn-danger"
                        onClick={() => handleDelete(p.user_id || p.userId)}
                      >
                        Delete Instance
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
