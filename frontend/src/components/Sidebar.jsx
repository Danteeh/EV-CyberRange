import { useState, useEffect } from 'react'
import { 
  Car, Zap, Server, Play, Square, RefreshCw, 
  Plus, Settings, Activity, Terminal, ExternalLink,
  ChevronDown, ChevronRight, Loader2, Shield, ShieldAlert,
  AlertTriangle, Skull
} from 'lucide-react'

// Standard components
const COMPONENT_TYPES = [
  { id: 'ev', label: 'Electric Vehicle', icon: Car, color: 'var(--cr-ev-body)' },
  { id: 'evse', label: 'Charge Point (EVSE)', icon: Zap, color: 'var(--cr-accent)' },
  { id: 'csms', label: 'CSMS Server', icon: Server, color: 'var(--cr-server)' },
]

// Vulnerable Charge Points for attack practice
const VULNERABLE_CP_TYPES = [
  { 
    id: 'hardy_barth', 
    label: 'Hardy Barth eCharge', 
    vendor: 'Hardy Barth',
    model: 'eCharge Salia',
    icon: ShieldAlert, 
    color: '#dc2626',
    port: 8081,
    cves: ['CVE-2024-11665', 'CVE-2024-11666'],
    vulns: ['RCE via PHP', 'MQTT without SSL'],
    difficulty: 'Easy'
  },
  { 
    id: 'schneider', 
    label: 'Schneider EVlink', 
    vendor: 'Schneider Electric',
    model: 'EVlink',
    icon: ShieldAlert, 
    color: '#dc2626',
    port: 8082,
    cves: ['CVE-2018-7800', 'CVE-2018-7801'],
    vulns: ['Code injection', 'Command execution'],
    difficulty: 'Medium'
  },
  { 
    id: 'wallbox', 
    label: 'Wallbox Pulsar', 
    vendor: 'Wallbox',
    model: 'Pulsar Plus',
    icon: ShieldAlert, 
    color: '#f59e0b',
    port: 8083,
    cves: ['CVE-2023-32249'],
    vulns: ['Unauthenticated API', 'No encryption'],
    difficulty: 'Easy'
  },
  { 
    id: 'chargepoint', 
    label: 'ChargePoint Flex', 
    vendor: 'ChargePoint',
    model: 'Home Flex',
    icon: Skull, 
    color: '#dc2626',
    port: 8084,
    cves: ['CVE-2022-26132'],
    vulns: ['Stack buffer overflow', 'DoS'],
    difficulty: 'Medium'
  },
  { 
    id: 'generic_web', 
    label: 'Generic WebConnect', 
    vendor: 'Generic EV',
    model: 'WebConnect Pro',
    icon: AlertTriangle, 
    color: '#f59e0b',
    port: 8085,
    cves: ['CVE-2024-43659'],
    vulns: ['Exposed credentials', 'Weak auth'],
    difficulty: 'Easy'
  },
  { 
    id: 'iso15118', 
    label: 'ISO 15118 Gateway', 
    vendor: 'ISO15118',
    model: 'PnC Gateway',
    icon: ShieldAlert, 
    color: '#7c3aed',
    port: 8086,
    cves: ['CVE-2025-12357'],
    vulns: ['MitM attack', 'No cert verification'],
    difficulty: 'Hard'
  },
]

export default function Sidebar() {
  const [activeSection, setActiveSection] = useState('control')

  return (
    <div className="sidebar-content">
      {/* Section tabs */}
      <div className="sidebar-tabs">
        <button 
          className={`sidebar-tab ${activeSection === 'control' ? 'active' : ''}`}
          onClick={() => setActiveSection('control')}
        >
          <Settings size={14} />
          Control
        </button>
        <button 
          className={`sidebar-tab ${activeSection === 'components' ? 'active' : ''}`}
          onClick={() => setActiveSection('components')}
        >
          <Plus size={14} />
          Add
        </button>
      </div>

      <div className="sidebar-body">
        {activeSection === 'components' && <ComponentsSection />}
        {activeSection === 'control' && <ControlSection />}
      </div>

      <style>{`
        .sidebar-content {
          display: flex;
          flex-direction: column;
          height: 100%;
        }
        .sidebar-tabs {
          display: flex;
          border-bottom: 1px solid var(--cr-border);
          flex-shrink: 0;
        }
        .sidebar-tab {
          flex: 1;
          padding: 10px 8px;
          background: transparent;
          border: none;
          border-bottom: 2px solid transparent;
          color: var(--cr-text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          font-size: 0.75rem;
          font-weight: 500;
          transition: all 0.15s;
        }
        .sidebar-tab:hover {
          background: var(--cr-surface2);
          color: var(--cr-text);
        }
        .sidebar-tab.active {
          color: var(--cr-accent);
          border-bottom-color: var(--cr-accent);
        }
        .sidebar-body {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }
      `}</style>
    </div>
  )
}

function ComponentsSection() {
  const handleDragStart = (e, type) => {
    e.dataTransfer.setData('componentType', type)
    e.dataTransfer.effectAllowed = 'copy'
  }

  const handleVulnDragStart = (e, vulnCp) => {
    e.dataTransfer.setData('componentType', 'vulnerable_evse')
    e.dataTransfer.setData('vulnCpData', JSON.stringify(vulnCp))
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <div>
      <div className="section-title">Standard Components</div>
      <div className="component-list">
        {COMPONENT_TYPES.map(comp => (
          <div
            key={comp.id}
            className="draggable-component"
            draggable
            onDragStart={(e) => handleDragStart(e, comp.id)}
          >
            <div className="component-icon" style={{ background: comp.color }}>
              <comp.icon size={18} />
            </div>
            <span className="component-label">{comp.label}</span>
          </div>
        ))}
      </div>

      <div className="section-divider" />

      <div className="section-title">
        <ShieldAlert size={12} style={{ marginRight: 4 }} />
        Vulnerable Targets (CVE Lab)
      </div>
      <div className="vuln-component-list">
        {VULNERABLE_CP_TYPES.map(comp => (
          <div
            key={comp.id}
            className="vuln-draggable-component"
            draggable
            onDragStart={(e) => handleVulnDragStart(e, comp)}
            title={`Port: ${comp.port}\nCVEs: ${comp.cves.join(', ')}`}
          >
            <div className="vuln-header">
              <div className="vuln-icon" style={{ background: comp.color }}>
                <comp.icon size={14} />
              </div>
              <div className="vuln-info">
                <span className="vuln-label">{comp.label}</span>
                <span className="vuln-cves">{comp.cves.join(', ')}</span>
              </div>
              <span className={`vuln-difficulty ${comp.difficulty.toLowerCase()}`}>
                {comp.difficulty}
              </span>
            </div>
            <div className="vuln-tags">
              {comp.vulns.map((v, i) => (
                <span key={i} className="vuln-tag">{v}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="section-divider" />

      <div className="section-title">Quick Links</div>
      <div className="quick-links">
        {VULNERABLE_CP_TYPES.map(comp => (
          <a 
            key={comp.id}
            href={`http://localhost:${comp.port}`}
            target="_blank"
            rel="noopener noreferrer"
            className="quick-link"
          >
            <ExternalLink size={12} />
            {comp.vendor} :{comp.port}
          </a>
        ))}
      </div>

      <style>{`
        .section-title {
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--cr-text-muted);
          margin-bottom: 12px;
          display: flex;
          align-items: center;
        }
        .section-divider {
          height: 1px;
          background: var(--cr-border);
          margin: 20px 0;
        }
        .component-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .draggable-component {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          cursor: grab;
          transition: all 0.15s;
        }
        .draggable-component:hover {
          background: var(--cr-surface3);
          border-color: var(--cr-border-light);
          transform: translateX(4px);
        }
        .draggable-component:active {
          cursor: grabbing;
        }
        .component-icon {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }
        .component-label {
          font-size: 0.8125rem;
          color: var(--cr-text);
        }

        /* Vulnerable components */
        .vuln-component-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .vuln-draggable-component {
          padding: 10px;
          background: var(--cr-surface2);
          border: 1px solid rgba(220, 38, 38, 0.3);
          border-radius: 6px;
          cursor: grab;
          transition: all 0.15s;
        }
        .vuln-draggable-component:hover {
          background: rgba(220, 38, 38, 0.1);
          border-color: rgba(220, 38, 38, 0.5);
          transform: translateX(4px);
        }
        .vuln-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }
        .vuln-icon {
          width: 24px;
          height: 24px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }
        .vuln-info {
          flex: 1;
          min-width: 0;
        }
        .vuln-label {
          display: block;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--cr-text);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .vuln-cves {
          display: block;
          font-size: 0.625rem;
          color: #dc2626;
          font-family: monospace;
        }
        .vuln-difficulty {
          font-size: 0.5625rem;
          font-weight: 600;
          padding: 2px 6px;
          border-radius: 3px;
          text-transform: uppercase;
          flex-shrink: 0;
        }
        .vuln-difficulty.easy {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }
        .vuln-difficulty.medium {
          background: rgba(245, 158, 11, 0.2);
          color: #f59e0b;
        }
        .vuln-difficulty.hard {
          background: rgba(124, 58, 237, 0.2);
          color: #7c3aed;
        }
        .vuln-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
        .vuln-tag {
          font-size: 0.5625rem;
          padding: 2px 6px;
          background: var(--cr-surface3);
          border-radius: 3px;
          color: var(--cr-text-muted);
        }

        /* Quick links */
        .quick-links {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .quick-link {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 8px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 4px;
          color: var(--cr-text-secondary);
          text-decoration: none;
          font-size: 0.6875rem;
          font-family: monospace;
          transition: all 0.15s;
        }
        .quick-link:hover {
          background: var(--cr-surface3);
          color: var(--cr-accent);
          border-color: var(--cr-accent);
        }

        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .action-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          color: var(--cr-text-secondary);
          cursor: pointer;
          font-size: 0.8125rem;
          transition: all 0.15s;
        }
        .action-btn:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
        }
      `}</style>
    </div>
  )
}

function ControlSection() {
  const [chargePoints, setChargePoints] = useState([])
  const [selectedCP, setSelectedCP] = useState('')
  const [selectedConnector, setSelectedConnector] = useState(1)
  const [idTag, setIdTag] = useState('TEST-USER')
  const [loading, setLoading] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [expanded, setExpanded] = useState({})

  // Fetch charge points from backend
  useEffect(() => {
    fetchChargePoints()
    const interval = setInterval(fetchChargePoints, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchChargePoints = async () => {
    try {
      const res = await fetch('/api/ocpp/charge-points')
      if (res.ok) {
        const data = await res.json()
        setChargePoints(data.charge_points || [])
        if (!selectedCP && data.charge_points?.length > 0) {
          setSelectedCP(data.charge_points[0].id)
        }
      }
    } catch (e) {
      console.error('Failed to fetch charge points:', e)
    }
  }

  const handleRemoteStart = async () => {
    if (!selectedCP) return
    setLoading(true)
    setLastResult(null)
    try {
      const res = await fetch('/api/ocpp/remote-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charge_point_id: selectedCP,
          id_tag: idTag,
          connector_id: selectedConnector
        })
      })
      const data = await res.json()
      setLastResult({ 
        type: data.status === 'Accepted' ? 'success' : 'error', 
        message: `RemoteStart: ${data.status}` 
      })
      // Refresh status
      setTimeout(fetchChargePoints, 1000)
    } catch (e) {
      setLastResult({ type: 'error', message: `Error: ${e.message}` })
    } finally {
      setLoading(false)
    }
  }

  const handleRemoteStop = async () => {
    if (!selectedCP) return
    setLoading(true)
    setLastResult(null)
    try {
      const res = await fetch('/api/ocpp/remote-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charge_point_id: selectedCP
          // No transaction_id - CSMS will find the active one
        })
      })
      const data = await res.json()
      setLastResult({ 
        type: data.status === 'Accepted' ? 'success' : 'error', 
        message: `RemoteStop: ${data.status}` 
      })
      setTimeout(fetchChargePoints, 1000)
    } catch (e) {
      setLastResult({ type: 'error', message: `Error: ${e.message}` })
    } finally {
      setLoading(false)
    }
  }

  const toggleExpand = (cpId) => {
    setExpanded(prev => ({ ...prev, [cpId]: !prev[cpId] }))
  }

  const getStatusColor = (status) => {
    const s = (status || '').toLowerCase()
    if (s === 'charging') return 'var(--cr-success)'
    if (s === 'available') return 'var(--cr-accent)'
    if (s === 'preparing' || s === 'finishing') return 'var(--cr-warning)'
    if (s === 'faulted' || s === 'unavailable') return 'var(--cr-danger)'
    return 'var(--cr-text-muted)'
  }

  // Get connector count from model name (e.g., EVCR-SIM-2C -> 2)
  const getConnectorCount = (cp) => {
    const match = cp.model?.match(/(\d+)C$/)
    return match ? parseInt(match[1]) : 1
  }

  return (
    <div>
      <div className="section-title">Remote Charging Control</div>
      
      {/* Charge Point Selector */}
      <div className="control-group">
        <label className="control-label">Charge Point</label>
        <select 
          className="control-select"
          value={selectedCP}
          onChange={(e) => {
            setSelectedCP(e.target.value)
            setSelectedConnector(1)
          }}
        >
          {chargePoints.length === 0 && (
            <option value="">No charge points connected</option>
          )}
          {chargePoints.map(cp => (
            <option key={cp.id} value={cp.id}>
              {cp.id} ({cp.status})
            </option>
          ))}
        </select>
      </div>

      {/* Connector Selector - show if CP has multiple connectors */}
      {selectedCP && (() => {
        const cp = chargePoints.find(c => c.id === selectedCP)
        const connCount = cp ? getConnectorCount(cp) : 1
        if (connCount > 1) {
          return (
            <div className="control-group">
              <label className="control-label">Connector</label>
              <select 
                className="control-select"
                value={selectedConnector}
                onChange={(e) => setSelectedConnector(parseInt(e.target.value))}
              >
                {Array.from({ length: connCount }, (_, i) => i + 1).map(n => (
                  <option key={n} value={n}>Connector {n}</option>
                ))}
              </select>
            </div>
          )
        }
        return null
      })()}

      {/* ID Tag */}
      <div className="control-group">
        <label className="control-label">ID Tag (RFID)</label>
        <input 
          type="text"
          className="control-input"
          value={idTag}
          onChange={(e) => setIdTag(e.target.value)}
          placeholder="User ID Tag"
        />
      </div>

      {/* Control Buttons */}
      <div className="control-buttons">
        <button 
          className="btn-control btn-start" 
          onClick={handleRemoteStart}
          disabled={loading || !selectedCP}
        >
          {loading ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
          Start
        </button>
        <button 
          className="btn-control btn-stop" 
          onClick={() => handleRemoteStop()}
          disabled={loading || !selectedCP}
        >
          {loading ? <Loader2 size={16} className="spin" /> : <Square size={16} />}
          Stop
        </button>
      </div>

      {/* Result Message */}
      {lastResult && (
        <div className={`result-message ${lastResult.type}`}>
          {lastResult.message}
        </div>
      )}

      <div className="section-divider" />

      {/* Connected Charge Points Status */}
      <div className="section-title">
        Connected Charge Points
        <button className="refresh-btn" onClick={fetchChargePoints}>
          <RefreshCw size={12} />
        </button>
      </div>

      <div className="cp-list">
        {chargePoints.length === 0 ? (
          <div className="no-cp">
            <Activity size={20} />
            <span>No charge points connected</span>
            <span className="hint">Start the lab with .\start.ps1</span>
          </div>
        ) : (
          chargePoints.map(cp => (
            <div key={cp.id} className="cp-card">
              <div className="cp-header" onClick={() => toggleExpand(cp.id)}>
                {expanded[cp.id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <Zap size={14} style={{ color: getStatusColor(cp.status) }} />
                <span className="cp-id">{cp.id}</span>
                <span 
                  className="cp-status"
                  style={{ color: getStatusColor(cp.status) }}
                >
                  {cp.status}
                </span>
              </div>
              {expanded[cp.id] && (
                <div className="cp-details">
                  <div className="cp-detail">
                    <span>Model:</span>
                    <span>{cp.model}</span>
                  </div>
                  <div className="cp-detail">
                    <span>Vendor:</span>
                    <span>{cp.vendor}</span>
                  </div>
                  <div className="cp-detail">
                    <span>Connectors:</span>
                    <span>{getConnectorCount(cp)}</span>
                  </div>
                  <div className="cp-detail">
                    <span>Active Sessions:</span>
                    <span>{cp.active_sessions || 0}</span>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="section-divider" />

      {/* Kali Link */}
      <div className="section-title">Security Testing</div>
      <a 
        href="http://localhost:6080/vnc.html?autoconnect=true" 
        target="_blank" 
        rel="noopener noreferrer"
        className="kali-link"
      >
        <Terminal size={18} />
        <div className="kali-text">
          <span className="kali-title">Open Kali Linux</span>
          <span className="kali-hint">Run attacks from the terminal</span>
        </div>
        <ExternalLink size={14} />
      </a>

      <style>{`
        .section-title {
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--cr-text-muted);
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .section-divider {
          height: 1px;
          background: var(--cr-border);
          margin: 20px 0;
        }
        .refresh-btn {
          background: none;
          border: none;
          color: var(--cr-text-muted);
          cursor: pointer;
          padding: 2px;
        }
        .refresh-btn:hover {
          color: var(--cr-accent);
        }
        .control-group {
          margin-bottom: 12px;
        }
        .control-label {
          display: block;
          font-size: 0.75rem;
          color: var(--cr-text-muted);
          margin-bottom: 6px;
        }
        .control-select, .control-input {
          width: 100%;
          padding: 8px 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          color: var(--cr-text);
          font-size: 0.8125rem;
          font-family: inherit;
        }
        .control-select:focus, .control-input:focus {
          outline: none;
          border-color: var(--cr-accent);
        }
        .control-buttons {
          display: flex;
          gap: 8px;
          margin-top: 16px;
        }
        .btn-control {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 10px;
          border: none;
          border-radius: 6px;
          font-weight: 500;
          font-size: 0.8125rem;
          cursor: pointer;
          transition: all 0.15s;
        }
        .btn-control:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .btn-start {
          background: var(--cr-success);
          color: white;
        }
        .btn-start:hover:not(:disabled) {
          filter: brightness(1.1);
        }
        .btn-stop {
          background: var(--cr-danger);
          color: white;
        }
        .btn-stop:hover:not(:disabled) {
          filter: brightness(1.1);
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .result-message {
          margin-top: 12px;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 0.8125rem;
        }
        .result-message.success {
          background: rgba(74, 159, 110, 0.15);
          color: var(--cr-success);
          border: 1px solid rgba(74, 159, 110, 0.3);
        }
        .result-message.error {
          background: rgba(196, 92, 92, 0.15);
          color: var(--cr-danger);
          border: 1px solid rgba(196, 92, 92, 0.3);
        }
        .cp-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .no-cp {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 24px;
          color: var(--cr-text-muted);
          text-align: center;
        }
        .no-cp .hint {
          font-size: 0.75rem;
          color: var(--cr-text-dim);
        }
        .cp-card {
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          overflow: hidden;
        }
        .cp-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          cursor: pointer;
          transition: background 0.15s;
        }
        .cp-header:hover {
          background: var(--cr-surface3);
        }
        .cp-id {
          font-size: 0.8125rem;
          font-weight: 500;
          color: var(--cr-text);
        }
        .cp-status {
          margin-left: auto;
          font-size: 0.75rem;
          font-weight: 500;
        }
        .cp-details {
          padding: 8px 12px 12px 32px;
          border-top: 1px solid var(--cr-border);
          background: var(--cr-surface);
        }
        .cp-detail {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          padding: 4px 0;
          color: var(--cr-text-muted);
        }
        .cp-detail span:last-child {
          color: var(--cr-text-secondary);
        }
        .kali-link {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
          border: 1px solid #4a5568;
          border-radius: 8px;
          color: #e2e8f0;
          text-decoration: none;
          transition: all 0.15s;
        }
        .kali-link:hover {
          border-color: #718096;
          transform: translateY(-1px);
        }
        .kali-text {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
        .kali-title {
          font-size: 0.875rem;
          font-weight: 500;
        }
        .kali-hint {
          font-size: 0.6875rem;
          color: #a0aec0;
        }
      `}</style>
    </div>
  )
}
