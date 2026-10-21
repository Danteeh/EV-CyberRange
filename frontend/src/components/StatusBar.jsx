import { useStore } from '../store'
import { Activity, AlertCircle, CheckCircle, Info } from 'lucide-react'

export default function StatusBar() {
  const { recentEvents, attacks } = useStore()
  const latestEvent = recentEvents?.[0]
  const activeAttacks = attacks?.filter(a => a.status === 'RUNNING')?.length || 0

  return (
    <footer className="status-bar">
      <div className="status-section">
        <Activity size={12} className="status-icon" />
        <span className="status-label">Latest:</span>
        {latestEvent ? (
          <span className="status-event">
            <EventIcon type={latestEvent.type} />
            {latestEvent.message || latestEvent.type}
          </span>
        ) : (
          <span className="status-event muted">No events yet</span>
        )}
      </div>

      {activeAttacks > 0 && (
        <div className="status-section status-warning">
          <AlertCircle size={12} />
          <span>{activeAttacks} attack{activeAttacks > 1 ? 's' : ''} in progress</span>
        </div>
      )}

      <div className="status-section status-right">
        <span className="status-time">
          {new Date().toLocaleTimeString()}
        </span>
      </div>

      <style>{`
        .status-bar {
          height: 28px;
          background: var(--cr-surface);
          border-top: 1px solid var(--cr-border);
          display: flex;
          align-items: center;
          padding: 0 16px;
          gap: 24px;
          font-size: 0.75rem;
          color: var(--cr-text-muted);
          flex-shrink: 0;
        }
        .status-section {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .status-icon {
          color: var(--cr-accent);
        }
        .status-label {
          color: var(--cr-text-dim);
        }
        .status-event {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--cr-text-secondary);
        }
        .status-event.muted {
          color: var(--cr-text-dim);
        }
        .status-warning {
          color: var(--cr-danger);
        }
        .status-right {
          margin-left: auto;
        }
        .status-time {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.6875rem;
        }
      `}</style>
    </footer>
  )
}

function EventIcon({ type }) {
  const iconProps = { size: 10 }
  
  switch (type) {
    case 'charging_started':
    case 'charging_stopped':
      return <CheckCircle {...iconProps} style={{ color: 'var(--cr-success)' }} />
    case 'error':
    case 'attack':
      return <AlertCircle {...iconProps} style={{ color: 'var(--cr-danger)' }} />
    default:
      return <Info {...iconProps} style={{ color: 'var(--cr-accent)' }} />
  }
}
