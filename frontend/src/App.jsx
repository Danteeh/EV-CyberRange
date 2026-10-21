import { useState, useEffect } from 'react'
import { useStore } from './store'
import TopologyCanvas from './components/TopologyCanvas'
import Sidebar from './components/Sidebar'
import EmbeddedPanel from './components/EmbeddedPanel'
import StatusBar from './components/StatusBar'
import { 
  Monitor, Terminal, Activity, Shield, Settings, 
  ChevronLeft, ChevronRight, Maximize2, Minimize2,
  Zap, Server, Car, Radio
} from 'lucide-react'

// Layout modes
const LAYOUTS = {
  topology: 'topology',      // Full topology view
  split: 'split',           // Topology + embedded panel
  embedded: 'embedded',     // Full embedded panel
}

// Embedded panel options
const EMBED_OPTIONS = [
  { id: 'kali', label: 'Kali Linux', icon: Terminal, url: 'http://localhost:6080/vnc.html?autoconnect=true&resize=scale' },
  { id: 'nodered', label: 'Node-RED', icon: Radio, url: 'http://localhost:1880' },
  { id: 'logs', label: 'OCPP Traffic', icon: Activity, url: null }, // Custom component
]

export default function App() {
  const { connectWS, wsConnected, connectivity } = useStore()
  const [layout, setLayout] = useState(LAYOUTS.topology)
  const [activeEmbed, setActiveEmbed] = useState(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  useEffect(() => { connectWS() }, [])

  const handleEmbedSelect = (embedId) => {
    if (activeEmbed === embedId) {
      // Toggle off
      setActiveEmbed(null)
      setLayout(LAYOUTS.topology)
    } else {
      setActiveEmbed(embedId)
      setLayout(LAYOUTS.split)
    }
  }

  const toggleFullEmbed = () => {
    setLayout(layout === LAYOUTS.embedded ? LAYOUTS.split : LAYOUTS.embedded)
  }

  return (
    <div className="app-container">
      {/* ═══════════════════════════════════════════════════════
          Top Bar
          ═══════════════════════════════════════════════════════ */}
      <header className="app-header">
        <div className="header-brand">
          <Zap size={20} className="brand-icon" />
          <span className="brand-text">EV-CyberRange</span>
          <span className="brand-version">v2.0</span>
        </div>

        <div className="header-status">
          <StatusIndicator 
            label="WebSocket" 
            status={wsConnected ? 'online' : 'offline'} 
          />
          <StatusIndicator 
            label="MQTT" 
            status={connectivity?.mqtt ? 'online' : 'offline'} 
          />
          <StatusIndicator 
            label="OCPP" 
            status={connectivity?.ocpp === 'CONNECTED' ? 'online' : 'offline'} 
          />
        </div>

        <div className="header-actions">
          {EMBED_OPTIONS.map(opt => (
            <button
              key={opt.id}
              className={`header-btn ${activeEmbed === opt.id ? 'active' : ''}`}
              onClick={() => handleEmbedSelect(opt.id)}
              title={opt.label}
            >
              <opt.icon size={16} />
              <span className="btn-label">{opt.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* ═══════════════════════════════════════════════════════
          Main Content Area
          ═══════════════════════════════════════════════════════ */}
      <main className="app-main">
        {/* Sidebar */}
        <aside className={`app-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
          {!sidebarCollapsed && <Sidebar />}
        </aside>

        {/* Content */}
        <div className="app-content">
          {layout === LAYOUTS.topology && (
            <div className="content-full">
              <TopologyCanvas />
            </div>
          )}

          {layout === LAYOUTS.split && (
            <>
              <div className="content-left">
                <TopologyCanvas />
              </div>
              <div className="content-right">
                <div className="embed-header">
                  <span>{EMBED_OPTIONS.find(o => o.id === activeEmbed)?.label}</span>
                  <div className="embed-controls">
                    <button onClick={toggleFullEmbed} title="Maximize">
                      <Maximize2 size={14} />
                    </button>
                    <button onClick={() => { setActiveEmbed(null); setLayout(LAYOUTS.topology); }} title="Close">
                      &times;
                    </button>
                  </div>
                </div>
                <EmbeddedPanel type={activeEmbed} />
              </div>
            </>
          )}

          {layout === LAYOUTS.embedded && (
            <div className="content-full">
              <div className="embed-header">
                <span>{EMBED_OPTIONS.find(o => o.id === activeEmbed)?.label}</span>
                <div className="embed-controls">
                  <button onClick={toggleFullEmbed} title="Exit fullscreen">
                    <Minimize2 size={14} />
                  </button>
                  <button onClick={() => { setActiveEmbed(null); setLayout(LAYOUTS.topology); }} title="Close">
                    &times;
                  </button>
                </div>
              </div>
              <EmbeddedPanel type={activeEmbed} />
            </div>
          )}
        </div>
      </main>

      {/* ═══════════════════════════════════════════════════════
          Status Bar
          ═══════════════════════════════════════════════════════ */}
      <StatusBar />

      <style>{`
        .app-container {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--cr-bg);
        }

        /* ─── Header ─── */
        .app-header {
          height: 48px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
          display: flex;
          align-items: center;
          padding: 0 16px;
          gap: 24px;
          flex-shrink: 0;
        }

        .header-brand {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .brand-icon {
          color: var(--cr-accent);
        }

        .brand-text {
          font-weight: 600;
          font-size: 1rem;
          color: var(--cr-text);
        }

        .brand-version {
          font-size: 0.7rem;
          color: var(--cr-text-dim);
          padding: 2px 6px;
          background: var(--cr-surface2);
          border-radius: 4px;
        }

        .header-status {
          display: flex;
          gap: 16px;
          margin-left: auto;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .header-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 6px;
          color: var(--cr-text-muted);
          cursor: pointer;
          transition: all 0.15s;
          font-size: 0.8125rem;
        }

        .header-btn:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
          border-color: var(--cr-border-light);
        }

        .header-btn.active {
          background: var(--cr-accent-dim);
          border-color: var(--cr-accent);
          color: var(--cr-text);
        }

        .btn-label {
          display: none;
        }

        @media (min-width: 1200px) {
          .btn-label { display: inline; }
        }

        /* ─── Main ─── */
        .app-main {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        /* ─── Sidebar ─── */
        .app-sidebar {
          width: 280px;
          background: var(--cr-surface);
          border-right: 1px solid var(--cr-border);
          display: flex;
          flex-direction: column;
          position: relative;
          transition: width 0.2s ease;
          flex-shrink: 0;
        }

        .app-sidebar.collapsed {
          width: 0;
          overflow: hidden;
        }

        .sidebar-toggle {
          position: absolute;
          right: -12px;
          top: 50%;
          transform: translateY(-50%);
          width: 24px;
          height: 48px;
          background: var(--cr-surface2);
          border: 1px solid var(--cr-border);
          border-radius: 0 6px 6px 0;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--cr-text-muted);
          z-index: 10;
        }

        .sidebar-toggle:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
        }

        /* ─── Content ─── */
        .app-content {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        .content-full {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .content-left {
          flex: 1;
          min-width: 400px;
          overflow: hidden;
        }

        .content-right {
          width: 50%;
          max-width: 800px;
          min-width: 400px;
          display: flex;
          flex-direction: column;
          border-left: 1px solid var(--cr-border);
          background: var(--cr-bg-deep);
        }

        .embed-header {
          height: 36px;
          background: var(--cr-surface);
          border-bottom: 1px solid var(--cr-border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 12px;
          font-size: 0.8125rem;
          font-weight: 500;
          color: var(--cr-text-secondary);
          flex-shrink: 0;
        }

        .embed-controls {
          display: flex;
          gap: 8px;
        }

        .embed-controls button {
          background: transparent;
          border: none;
          color: var(--cr-text-muted);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
        }

        .embed-controls button:hover {
          background: var(--cr-surface2);
          color: var(--cr-text);
        }
      `}</style>
    </div>
  )
}

function StatusIndicator({ label, status }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div 
        className={`status-dot ${status}`}
        style={status === 'online' ? { boxShadow: '0 0 6px var(--cr-success)' } : {}}
      />
      <span style={{ fontSize: '0.75rem', color: 'var(--cr-text-muted)' }}>{label}</span>
    </div>
  )
}
