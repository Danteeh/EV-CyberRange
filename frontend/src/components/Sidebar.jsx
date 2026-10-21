import { useState } from 'react'
import { useStore } from '../store'
import { 
  Car, Zap, Server, Play, Square, RefreshCw, 
  Plus, Trash2, Settings, Shield, Activity,
  ChevronDown, ChevronRight, AlertTriangle
} from 'lucide-react'

const COMPONENT_TYPES = [
  { id: 'ev', label: 'Electric Vehicle', icon: Car, color: 'var(--cr-ev-body)' },
  { id: 'evse', label: 'Charge Point (EVSE)', icon: Zap, color: 'var(--cr-accent)' },
  { id: 'csms', label: 'CSMS Server', icon: Server, color: 'var(--cr-server)' },
]

export default function Sidebar() {
  const [activeSection, setActiveSection] = useState('components')

  return (
    <div className="sidebar-content">
      {/* Section tabs */}
      <div className="sidebar-tabs">
        <button 
          className={`sidebar-tab ${activeSection === 'components' ? 'active' : ''}`}
          onClick={() => setActiveSection('components')}
        >
          <Plus size={14} />
          Components
        </button>
        <button 
          className={`sidebar-tab ${activeSection === 'control' ? 'active' : ''}`}
          onClick={() => setActiveSection('control')}
        >
          <Settings size={14} />
          Control
        </button>
        <button 
          className={`sidebar-tab ${activeSection === 'attacks' ? 'active' : ''}`}
          onClick={() => setActiveSection('attacks')}
        >
          <Shield size={14} />
          Attacks
        </button>
      </div>

      <div className="sidebar-body">
        {activeSection === 'components' && <ComponentsSection />}
        {activeSection === 'control' && <ControlSection />}
        {activeSection === 'attacks' && <AttacksSection />}
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

  return (
    <div>
      <div className="section-title">Drag to Canvas</div>
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

      <div className="section-title">Quick Actions</div>
      <div className="quick-actions">
        <button className="action-btn">
          <Play size={14} />
          Start All
        </button>
        <button className="action-btn">
          <Square size={14} />
          Stop All
        </button>
        <button className="action-btn">
          <RefreshCw size={14} />
          Reset Topology
        </button>
      </div>

      <style>{`
        .section-title {
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--cr-text-muted);
          margin-bottom: 12px;
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
  const { connectors, sendControl } = useStore()
  const [selectedCP, setSelectedCP] = useState('EVCR-001')

  const handleRemoteStart = async () => {
    try {
      const res = await fetch('/api/ocpp/remote-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charge_point_id: selectedCP,
          id_tag: 'FRONTEND-USER',
          connector_id: 1
        })
      })
      const data = await res.json()
      console.log('RemoteStart:', data)
    } catch (e) {
      console.error('RemoteStart failed:', e)
    }
  }

  const handleRemoteStop = async () => {
    try {
      const res = await fetch('/api/ocpp/remote-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          charge_point_id: selectedCP,
          transaction_id: 1001
        })
      })
      const data = await res.json()
      console.log('RemoteStop:', data)
    } catch (e) {
      console.error('RemoteStop failed:', e)
    }
  }

  return (
    <div>
      <div className="section-title">Charge Point Control</div>
      
      <div className="control-group">
        <label className="control-label">Select Charge Point</label>
        <select 
          className="control-select"
          value={selectedCP}
          onChange={(e) => setSelectedCP(e.target.value)}
        >
          <option value="EVCR-001">EVCR-001</option>
          <option value="EVCR-002">EVCR-002</option>
        </select>
      </div>

      <div className="control-buttons">
        <button className="btn-control btn-start" onClick={handleRemoteStart}>
          <Play size={16} />
          Start Charging
        </button>
        <button className="btn-control btn-stop" onClick={handleRemoteStop}>
          <Square size={16} />
          Stop Charging
        </button>
      </div>

      <div className="section-divider" />

      <div className="section-title">Charge Point Status</div>
      <div className="status-cards">
        {Object.entries(connectors || {}).map(([id, data]) => (
          <div key={id} className="status-card">
            <div className="status-header">
              <Zap size={14} />
              <span>Connector {id}</span>
              <span className={`status-badge ${data?.state?.toLowerCase() || 'unknown'}`}>
                {data?.state || 'Unknown'}
              </span>
            </div>
            {data?.metrics && (
              <div className="status-metrics">
                <div className="metric">
                  <span className="metric-value">{(data.metrics.power_w || 0).toFixed(0)}</span>
                  <span className="metric-unit">W</span>
                </div>
                <div className="metric">
                  <span className="metric-value">{((data.metrics.energy_wh || 0) / 1000).toFixed(2)}</span>
                  <span className="metric-unit">kWh</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{`
        .control-group {
          margin-bottom: 16px;
        }
        .control-label {
          display: block;
          font-size: 0.75rem;
          color: var(--cr-text-muted);
          margin-bottom: 6px;
        }
        .control-select {
          width: 100%;
          padding: 8px 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          color: var(--cr-text);
          font-size: 0.875rem;
        }
        .control-select:focus {
          outline: none;
          border-color: var(--cr-accent);
        }
        .control-buttons {
          display: flex;
          gap: 8px;
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
        .btn-start {
          background: var(--cr-success);
          color: white;
        }
        .btn-start:hover {
          background: var(--cr-success-dim);
        }
        .btn-stop {
          background: var(--cr-danger);
          color: white;
        }
        .btn-stop:hover {
          background: var(--cr-danger-dim);
        }
        .status-cards {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .status-card {
          padding: 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
        }
        .status-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--cr-text-secondary);
          font-size: 0.8125rem;
        }
        .status-badge {
          margin-left: auto;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.6875rem;
          font-weight: 500;
          text-transform: uppercase;
        }
        .status-badge.charging {
          background: rgba(74, 159, 110, 0.2);
          color: var(--cr-success);
        }
        .status-badge.available {
          background: rgba(77, 166, 168, 0.2);
          color: var(--cr-accent);
        }
        .status-badge.preparing, .status-badge.suspended {
          background: rgba(201, 145, 58, 0.2);
          color: var(--cr-warning);
        }
        .status-badge.faulted {
          background: rgba(196, 92, 92, 0.2);
          color: var(--cr-danger);
        }
        .status-metrics {
          display: flex;
          gap: 16px;
          margin-top: 8px;
        }
        .metric {
          display: flex;
          align-items: baseline;
          gap: 4px;
        }
        .metric-value {
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--cr-text);
        }
        .metric-unit {
          font-size: 0.75rem;
          color: var(--cr-text-muted);
        }
      `}</style>
    </div>
  )
}

function AttacksSection() {
  const [attacks, setAttacks] = useState([
    { id: 'replay', name: 'OCPP Replay Attack', desc: 'Capture and replay RemoteStart commands', status: 'ready' },
    { id: 'mitm', name: 'ARP Spoofing MitM', desc: 'Intercept traffic between CP and CSMS', status: 'ready' },
    { id: 'fuzzing', name: 'OCPP Message Fuzzing', desc: 'Send malformed OCPP messages', status: 'ready' },
    { id: 'dos', name: 'Connection Flood', desc: 'Exhaust CSMS connection pool', status: 'ready' },
  ])

  const startAttack = (attackId) => {
    setAttacks(attacks.map(a => 
      a.id === attackId ? { ...a, status: 'running' } : a
    ))
  }

  const stopAttack = (attackId) => {
    setAttacks(attacks.map(a => 
      a.id === attackId ? { ...a, status: 'ready' } : a
    ))
  }

  return (
    <div>
      <div className="section-title">Security Testing</div>
      
      <div className="attack-warning">
        <AlertTriangle size={14} />
        <span>Attacks affect the simulated environment only</span>
      </div>

      <div className="attack-list">
        {attacks.map(attack => (
          <div key={attack.id} className={`attack-card ${attack.status}`}>
            <div className="attack-header">
              <Shield size={14} />
              <span className="attack-name">{attack.name}</span>
              <span className={`attack-status ${attack.status}`}>
                {attack.status === 'running' ? 'Running' : 'Ready'}
              </span>
            </div>
            <p className="attack-desc">{attack.desc}</p>
            <div className="attack-actions">
              {attack.status === 'ready' ? (
                <button 
                  className="btn-attack btn-start-attack"
                  onClick={() => startAttack(attack.id)}
                >
                  <Play size={12} />
                  Launch
                </button>
              ) : (
                <button 
                  className="btn-attack btn-stop-attack"
                  onClick={() => stopAttack(attack.id)}
                >
                  <Square size={12} />
                  Stop
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .attack-warning {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: rgba(201, 145, 58, 0.1);
          border: 1px solid rgba(201, 145, 58, 0.3);
          border-radius: 6px;
          color: var(--cr-warning);
          font-size: 0.75rem;
          margin-bottom: 16px;
        }
        .attack-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .attack-card {
          padding: 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          transition: all 0.15s;
        }
        .attack-card.running {
          border-color: var(--cr-danger);
          background: rgba(196, 92, 92, 0.1);
        }
        .attack-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--cr-text-secondary);
          font-size: 0.8125rem;
        }
        .attack-name {
          font-weight: 500;
          color: var(--cr-text);
        }
        .attack-status {
          margin-left: auto;
          font-size: 0.6875rem;
          font-weight: 500;
          text-transform: uppercase;
        }
        .attack-status.ready {
          color: var(--cr-text-muted);
        }
        .attack-status.running {
          color: var(--cr-danger);
        }
        .attack-desc {
          font-size: 0.75rem;
          color: var(--cr-text-muted);
          margin: 8px 0;
        }
        .attack-actions {
          display: flex;
          gap: 8px;
        }
        .btn-attack {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border: none;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }
        .btn-start-attack {
          background: var(--cr-danger);
          color: white;
        }
        .btn-stop-attack {
          background: var(--cr-surface3);
          color: var(--cr-text);
          border: 1px solid var(--cr-border);
        }
      `}</style>
    </div>
  )
}
