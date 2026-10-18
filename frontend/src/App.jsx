import { useEffect } from 'react'
import { useStore } from './store'
import TopBar from './components/TopBar'
import TopologyView from './components/TopologyView'
import ControlPanel from './components/ControlPanel'
import AttacksPanel from './components/AttacksPanel'
import EventsPanel from './components/EventsPanel'
import { Terminal, Crosshair, Activity } from 'lucide-react'

const PANELS = [
  { id: 'control', label: 'CONTROL', icon: Terminal },
  { id: 'attacks', label: 'ATTACKS', icon: Crosshair },
  { id: 'events',  label: 'EVENTS',  icon: Activity  },
]

export default function App() {
  const { connectWS, activePanel, setActivePanel } = useStore()

  useEffect(() => { connectWS() }, [])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <TopBar />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── Centro: vista 2.5D ── */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <TopologyView />
        </div>

        {/* ── Derecha: panel lateral ── */}
        <div style={{
          width: '300px',
          display: 'flex',
          flexDirection: 'column',
          borderLeft: '1px solid var(--cr-border)',
          background: 'var(--cr-surface)',
          flexShrink: 0,
          overflow: 'hidden',
        }}>

          {/* Tab bar */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--cr-border)',
            flexShrink: 0,
          }}>
            {PANELS.map(({ id, label, icon: Icon }) => {
              const active = activePanel === id
              return (
                <button
                  key={id}
                  onClick={() => setActivePanel(id)}
                  style={{
                    flex: 1,
                    padding: '8px 4px',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px',
                    background: active ? 'rgba(0,212,255,0.06)' : 'transparent',
                    border: 'none',
                    borderBottom: `2px solid ${active ? 'var(--cr-accent)' : 'transparent'}`,
                    color: active ? 'var(--cr-accent)' : 'var(--cr-text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.6rem',
                    fontFamily: 'monospace',
                    letterSpacing: '0.06em',
                    transition: 'all 0.15s',
                  }}
                >
                  <Icon size={14} />
                  {label}
                </button>
              )
            })}
          </div>

          {/* Panel content */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {activePanel === 'control' && <ControlPanel />}
            {activePanel === 'attacks' && <AttacksPanel />}
            {activePanel === 'events'  && <EventsPanel />}
          </div>
        </div>
      </div>
    </div>
  )
}
