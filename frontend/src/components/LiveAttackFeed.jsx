import { useState, useEffect, useRef } from 'react'
import { 
  Skull, AlertTriangle, Shield, Terminal, 
  ChevronDown, ChevronUp, Zap, Server,
  Eye, EyeOff, Trash2, Download, Play, Pause
} from 'lucide-react'

// Severity configuration
const SEVERITY_CONFIG = {
  critical: { 
    color: '#ef4444', 
    bg: 'rgba(239, 68, 68, 0.15)',
    border: 'rgba(239, 68, 68, 0.4)',
    icon: Skull 
  },
  high: { 
    color: '#f97316', 
    bg: 'rgba(249, 115, 22, 0.15)',
    border: 'rgba(249, 115, 22, 0.4)',
    icon: AlertTriangle 
  },
  medium: { 
    color: '#f59e0b', 
    bg: 'rgba(245, 158, 11, 0.15)',
    border: 'rgba(245, 158, 11, 0.4)',
    icon: Shield 
  },
  low: { 
    color: '#10b981', 
    bg: 'rgba(16, 185, 129, 0.15)',
    border: 'rgba(16, 185, 129, 0.4)',
    icon: Shield 
  },
  info: { 
    color: '#6b7280', 
    bg: 'rgba(107, 114, 128, 0.15)',
    border: 'rgba(107, 114, 128, 0.4)',
    icon: Terminal 
  },
}

// Attack type icons
const ATTACK_ICONS = {
  rce: Skull,
  dos: AlertTriangle,
  auth_bypass: Shield,
  credential_exposure: Eye,
  mitm: Zap,
  command_injection: Terminal,
  default: Skull,
}

export default function LiveAttackFeed() {
  const [events, setEvents] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [filter, setFilter] = useState('all')
  const [expandedId, setExpandedId] = useState(null)
  const feedRef = useRef(null)
  const eventSourceRef = useRef(null)

  // Connect to SSE stream
  useEffect(() => {
    if (isPaused) return

    const connectSSE = () => {
      const eventSource = new EventSource('/api/attack-feed/stream')
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setIsConnected(true)
      }

      eventSource.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          setEvents(prev => {
            const newEvents = [...prev, { ...event, id: Date.now() + Math.random() }]
            // Keep last 200 events
            return newEvents.slice(-200)
          })
        } catch (err) {
          console.error('Failed to parse event:', err)
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        eventSource.close()
        // Reconnect after 2 seconds
        setTimeout(connectSSE, 2000)
      }
    }

    connectSSE()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [isPaused])

  // Auto-scroll to bottom
  useEffect(() => {
    if (feedRef.current && !isPaused) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [events, isPaused])

  // Filter events
  const filteredEvents = events.filter(e => {
    if (filter === 'all') return true
    return e.severity === filter || e.attack_type === filter
  })

  const clearEvents = () => setEvents([])

  const exportEvents = () => {
    const data = JSON.stringify(events, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `attack-log-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="live-attack-feed">
      {/* Header */}
      <div className="feed-header">
        <div className="feed-title">
          <Skull size={16} className={isConnected ? 'pulse' : ''} />
          <span>Live Attack Feed</span>
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'LIVE' : 'DISCONNECTED'}
          </span>
        </div>
        
        <div className="feed-controls">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Events</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="rce">RCE</option>
            <option value="dos">DoS</option>
            <option value="mitm">MitM</option>
          </select>

          <button 
            className={`control-btn ${isPaused ? 'paused' : ''}`}
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play size={14} /> : <Pause size={14} />}
          </button>
          
          <button 
            className="control-btn"
            onClick={clearEvents}
            title="Clear"
          >
            <Trash2 size={14} />
          </button>
          
          <button 
            className="control-btn"
            onClick={exportEvents}
            title="Export"
          >
            <Download size={14} />
          </button>
        </div>
      </div>

      {/* Event Counter */}
      <div className="event-stats">
        <span className="stat">
          <span className="stat-count">{events.length}</span> total
        </span>
        <span className="stat critical">
          <span className="stat-count">
            {events.filter(e => e.severity === 'critical').length}
          </span> critical
        </span>
        <span className="stat high">
          <span className="stat-count">
            {events.filter(e => e.severity === 'high').length}
          </span> high
        </span>
      </div>

      {/* Event Feed */}
      <div className="feed-container" ref={feedRef}>
        {filteredEvents.length === 0 ? (
          <div className="no-events">
            <Terminal size={32} />
            <p>No attack events yet</p>
            <p className="hint">
              Run an exploit from Kali to see live activity
            </p>
          </div>
        ) : (
          filteredEvents.map((event) => (
            <AttackEvent 
              key={event.id} 
              event={event}
              expanded={expandedId === event.id}
              onToggle={() => setExpandedId(expandedId === event.id ? null : event.id)}
            />
          ))
        )}
      </div>

      <style>{`
        .live-attack-feed {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--cr-bg-deep);
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
        }

        .feed-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
        }

        .feed-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--cr-text);
        }

        .feed-title svg {
          color: #ef4444;
        }

        .feed-title svg.pulse {
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .connection-status {
          font-size: 0.625rem;
          font-weight: 700;
          padding: 2px 8px;
          border-radius: 4px;
          letter-spacing: 0.05em;
        }

        .connection-status.connected {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
          animation: blink 1s ease-in-out infinite;
        }

        .connection-status.disconnected {
          background: rgba(107, 114, 128, 0.2);
          color: #6b7280;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }

        .feed-controls {
          display: flex;
          gap: 8px;
        }

        .filter-select {
          padding: 4px 8px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 4px;
          color: var(--cr-text);
          font-size: 0.75rem;
          font-family: inherit;
        }

        .control-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 4px;
          color: var(--cr-text-muted);
          cursor: pointer;
          transition: all 0.15s;
        }

        .control-btn:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
        }

        .control-btn.paused {
          background: rgba(239, 68, 68, 0.2);
          border-color: #ef4444;
          color: #ef4444;
        }

        .event-stats {
          display: flex;
          gap: 16px;
          padding: 8px 16px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
          font-size: 0.6875rem;
        }

        .stat {
          color: var(--cr-text-muted);
        }

        .stat-count {
          font-weight: 700;
          color: var(--cr-text);
        }

        .stat.critical .stat-count {
          color: #ef4444;
        }

        .stat.high .stat-count {
          color: #f97316;
        }

        .feed-container {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }

        .no-events {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--cr-text-muted);
          text-align: center;
          gap: 8px;
        }

        .no-events p {
          margin: 0;
          font-size: 0.875rem;
        }

        .no-events .hint {
          font-size: 0.75rem;
          color: var(--cr-text-dim);
        }
      `}</style>
    </div>
  )
}

function AttackEvent({ event, expanded, onToggle }) {
  const severity = event.severity || 'info'
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.info
  const Icon = ATTACK_ICONS[event.attack_type] || config.icon

  const formatTime = (ts) => {
    if (!ts) return '--:--:--'
    const d = new Date(ts)
    return d.toLocaleTimeString('en-US', { hour12: false })
  }

  return (
    <div 
      className="attack-event"
      style={{ 
        background: config.bg,
        borderColor: config.border,
      }}
      onClick={onToggle}
    >
      <div className="event-main">
        <div className="event-icon" style={{ color: config.color }}>
          <Icon size={14} />
        </div>
        
        <div className="event-content">
          <div className="event-header">
            <span className="event-cve" style={{ color: config.color }}>
              {event.cve || event.attack_type || 'ATTACK'}
            </span>
            <span className="event-target">
              {event.target || event.source || 'unknown'}
            </span>
            <span className="event-time">
              {formatTime(event.timestamp)}
            </span>
          </div>
          
          <div className="event-message">
            {event.message || event.action || 'Attack event'}
          </div>
        </div>

        <button className="expand-btn">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {expanded && event.details && (
        <div className="event-details">
          <pre>{typeof event.details === 'string' 
            ? event.details 
            : JSON.stringify(event.details, null, 2)
          }</pre>
        </div>
      )}

      <style>{`
        .attack-event {
          margin-bottom: 6px;
          padding: 8px 12px;
          border: 1px solid;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
        }

        .attack-event:hover {
          filter: brightness(1.1);
        }

        .event-main {
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }

        .event-icon {
          flex-shrink: 0;
          margin-top: 2px;
        }

        .event-content {
          flex: 1;
          min-width: 0;
        }

        .event-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .event-cve {
          font-size: 0.6875rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .event-target {
          font-size: 0.625rem;
          color: var(--cr-text-muted);
          padding: 1px 6px;
          background: rgba(0,0,0,0.2);
          border-radius: 3px;
        }

        .event-time {
          margin-left: auto;
          font-size: 0.625rem;
          color: var(--cr-text-dim);
        }

        .event-message {
          font-size: 0.75rem;
          color: var(--cr-text-secondary);
          line-height: 1.4;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .expand-btn {
          background: none;
          border: none;
          color: var(--cr-text-muted);
          cursor: pointer;
          padding: 2px;
        }

        .event-details {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }

        .event-details pre {
          font-size: 0.6875rem;
          color: var(--cr-text-secondary);
          margin: 0;
          white-space: pre-wrap;
          word-break: break-all;
        }
      `}</style>
    </div>
  )
}
