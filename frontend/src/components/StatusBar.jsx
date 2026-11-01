import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { Activity, CheckCircle, Zap, Clock } from 'lucide-react'

export default function StatusBar() {
  const { connectivity, chargePoints } = useStore()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const chargingCount = chargePoints?.filter(cp => 
    cp.status?.toLowerCase() === 'charging'
  ).length || 0

  const availableCount = chargePoints?.filter(cp => 
    cp.status?.toLowerCase() === 'available'
  ).length || 0

  const servicesOnline = Object.values(connectivity || {}).filter(Boolean).length
  const totalServices = Object.keys(connectivity || {}).length

  return (
    <footer className="status-bar">
      <div className="status-section">
        <Activity size={12} className="status-icon" />
        <span className="status-label">Services:</span>
        <span className={`status-value ${servicesOnline === totalServices ? 'good' : 'warn'}`}>
          {servicesOnline}/{totalServices} online
        </span>
      </div>

      <div className="status-section">
        <Zap size={12} className="status-icon charging" />
        <span className="status-label">Charge Points:</span>
        <span className="status-value">
          {chargingCount > 0 && (
            <span className="charging-badge">{chargingCount} charging</span>
          )}
          {availableCount > 0 && (
            <span className="available-badge">{availableCount} available</span>
          )}
          {chargePoints?.length === 0 && (
            <span className="offline-badge">none connected</span>
          )}
        </span>
      </div>

      <div className="status-section status-right">
        <Clock size={12} />
        <span className="status-time">
          {time.toLocaleTimeString()}
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
          color: var(--cr-text-dim);
        }
        .status-icon.charging {
          color: var(--cr-success);
        }
        .status-label {
          color: var(--cr-text-dim);
        }
        .status-value {
          color: var(--cr-text-secondary);
          display: flex;
          gap: 8px;
        }
        .status-value.good {
          color: var(--cr-success);
        }
        .status-value.warn {
          color: var(--cr-warning);
        }
        .charging-badge {
          color: var(--cr-success);
          font-weight: 500;
        }
        .available-badge {
          color: var(--cr-accent);
        }
        .offline-badge {
          color: var(--cr-text-dim);
        }
        .status-right {
          margin-left: auto;
        }
        .status-time {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.6875rem;
          color: var(--cr-text-dim);
        }
      `}</style>
    </footer>
  )
}
