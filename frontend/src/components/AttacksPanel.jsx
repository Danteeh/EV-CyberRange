import { useEffect } from 'react'
import { useStore } from '../store'
import { Skull, Square, ChevronRight } from 'lucide-react'

const SEVERITY_COLOR = {
  INFO: '#10b981', WARNING: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444',
}

export default function AttacksPanel() {
  const { attackScenarios, attacks, loadScenarios, startAttack, stopAttack } = useStore()

  useEffect(() => { loadScenarios() }, [])

  const activeIds = new Set(attacks.filter(a => a.status === 'RUNNING').map(a => a.id))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '1rem' }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', letterSpacing: '0.08em' }}>
        ATTACK SCENARIOS
      </div>

      {attackScenarios.map(sc => {
        const running = activeIds.has(sc.id)
        const color = SEVERITY_COLOR[sc.severity] ?? '#9ca3af'
        return (
          <div
            key={sc.id}
            className={running ? 'anim-fade-in' : ''}
            style={{
              padding: '10px 12px', borderRadius: '8px',
              border: `1px solid ${running ? color : 'var(--cr-border)'}`,
              background: running ? `${color}11` : 'var(--cr-surface2)',
              transition: 'border-color 0.2s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Skull size={13} color={color} className={running ? 'anim-pulse-dot' : ''} />
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: running ? color : 'var(--cr-text)' }}>
                  {sc.name}
                </span>
              </div>
              <span style={{
                fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px',
                background: `${color}22`, color, border: `1px solid ${color}44`,
              }}>
                {sc.severity}
              </span>
            </div>

            <p style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', margin: '4px 0 8px', lineHeight: 1.4 }}>
              {sc.description}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.68rem', color: 'var(--cr-text-muted)' }}>
                <ChevronRight size={10} style={{ display: 'inline' }} /> {sc.target}
              </span>
              <button
                onClick={() => running ? stopAttack(sc.id) : startAttack(sc.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '4px 10px', borderRadius: '5px', cursor: 'pointer',
                  fontSize: '0.72rem', fontFamily: 'monospace',
                  border: `1px solid ${color}`,
                  background: running ? `${color}22` : 'transparent',
                  color,
                }}
              >
                {running ? <><Square size={11} /> STOP</> : <><Skull size={11} /> LAUNCH</>}
              </button>
            </div>

            {/* Progreso si está activo */}
            {running && (() => {
              const active = attacks.find(a => a.id === sc.id)
              return active ? (
                <div style={{ marginTop: '6px', fontSize: '0.68rem', color: 'var(--cr-text-muted)' }}>
                  Events generated: {active.events_generated}
                </div>
              ) : null
            })()}
          </div>
        )
      })}

      {attackScenarios.length === 0 && (
        <div style={{ textAlign: 'center', color: 'var(--cr-text-muted)', fontSize: '0.78rem', padding: '2rem 0' }}>
          Loading scenarios...
        </div>
      )}
    </div>
  )
}
