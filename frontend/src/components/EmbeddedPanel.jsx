import { useState, useEffect, useRef } from 'react'
import { RefreshCw, ExternalLink, Download } from 'lucide-react'

const EMBED_URLS = {
  kali: 'http://localhost:6080/vnc.html?autoconnect=true&resize=scale',
  nodered: 'http://localhost:1880',
}

export default function EmbeddedPanel({ type }) {
  if (type === 'logs') {
    return <OCPPLogsPanel />
  }

  const url = EMBED_URLS[type]
  if (!url) return null

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="embed-toolbar">
        <a href={url} target="_blank" rel="noopener noreferrer" className="toolbar-btn">
          <ExternalLink size={14} />
          Open in new tab
        </a>
      </div>
      <iframe
        src={url}
        className="embed-frame"
        style={{ flex: 1 }}
        allow="clipboard-write; clipboard-read"
        sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
      />
      <style>{`
        .embed-toolbar {
          padding: 8px 12px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
          display: flex;
          gap: 8px;
        }
        .toolbar-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 4px;
          color: var(--cr-text-muted);
          text-decoration: none;
          font-size: 0.75rem;
          cursor: pointer;
        }
        .toolbar-btn:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
        }
      `}</style>
    </div>
  )
}

function OCPPLogsPanel() {
  const [logs, setLogs] = useState([])
  const [autoScroll, setAutoScroll] = useState(true)
  const [filter, setFilter] = useState('')
  const logsRef = useRef(null)

  useEffect(() => {
    // Fetch initial logs
    fetchLogs()
    // Poll for new logs
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (autoScroll && logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/ocpp/logs?lines=100')
      if (res.ok) {
        const data = await res.json()
        setLogs(data.logs || [])
      }
    } catch (e) {
      // If API doesn't exist yet, try reading from shared file via backend
      console.log('OCPP logs API not available')
    }
  }

  const filteredLogs = filter 
    ? logs.filter(l => l.toLowerCase().includes(filter.toLowerCase()))
    : logs

  const highlightLog = (line) => {
    // Color different OCPP message types
    if (line.includes('RemoteStart') || line.includes('RemoteStop')) {
      return { color: 'var(--cr-warning)' }
    }
    if (line.includes('StartTransaction') || line.includes('StopTransaction')) {
      return { color: 'var(--cr-success)' }
    }
    if (line.includes('Authorize')) {
      return { color: 'var(--cr-info)' }
    }
    if (line.includes('BootNotification')) {
      return { color: 'var(--cr-accent)' }
    }
    if (line.includes('Heartbeat')) {
      return { color: 'var(--cr-text-dim)' }
    }
    if (line.includes('ERROR') || line.includes('error')) {
      return { color: 'var(--cr-danger)' }
    }
    return {}
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="logs-toolbar">
        <input
          type="text"
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="logs-filter"
        />
        <label className="logs-checkbox">
          <input 
            type="checkbox" 
            checked={autoScroll} 
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto-scroll
        </label>
        <button onClick={fetchLogs} className="toolbar-btn">
          <RefreshCw size={14} />
        </button>
      </div>

      <div ref={logsRef} className="logs-container">
        {filteredLogs.length === 0 ? (
          <div className="logs-empty">
            No OCPP traffic captured yet.
            <br />
            <span style={{ color: 'var(--cr-text-dim)' }}>
              Generate traffic with a RemoteStart command
            </span>
          </div>
        ) : (
          filteredLogs.map((line, i) => (
            <div key={i} className="log-line" style={highlightLog(line)}>
              {line}
            </div>
          ))
        )}
      </div>

      <style>{`
        .logs-toolbar {
          padding: 8px 12px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
          display: flex;
          gap: 12px;
          align-items: center;
        }
        .logs-filter {
          flex: 1;
          padding: 6px 10px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 4px;
          color: var(--cr-text);
          font-size: 0.8125rem;
          font-family: inherit;
        }
        .logs-filter:focus {
          outline: none;
          border-color: var(--cr-accent);
        }
        .logs-checkbox {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.75rem;
          color: var(--cr-text-muted);
          cursor: pointer;
        }
        .logs-container {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
          font-size: 0.75rem;
          line-height: 1.6;
          background: var(--cr-bg-deep);
        }
        .logs-empty {
          color: var(--cr-text-muted);
          text-align: center;
          padding: 40px;
        }
        .log-line {
          padding: 2px 0;
          color: var(--cr-text-secondary);
          white-space: pre-wrap;
          word-break: break-all;
        }
        .log-line:hover {
          background: var(--cr-surface);
        }
      `}</style>
    </div>
  )
}
