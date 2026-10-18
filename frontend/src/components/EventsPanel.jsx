import { useStore } from '../store'

const SEV_COLOR = {
  INFO: '#10b981', WARNING: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444',
}
const TYPE_ICON = {
  MQTT_EVENT: '📡', EVSE_SESSION: '🔌', OCPP_TRANSACTION: '💳',
  OCPP_MESSAGE: '📨', SECURITY_EVENT: '🔐', CONTROL_CMD: '🎮',
  ATTACK_EVENT: '💀', SYSTEM: '⚙️',
}

export default function EventsPanel() {
  const { recentEvents } = useStore()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '8px 1rem', fontSize: '0.7rem', color: 'var(--cr-text-muted)',
        letterSpacing: '0.08em', borderBottom: '1px solid var(--cr-border)',
        display: 'flex', justifyContent: 'space-between',
      }}>
        <span>EVENT LOG</span>
        <span style={{ color: 'var(--cr-accent)' }}>{recentEvents.length} recent</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
        {recentEvents.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--cr-text-muted)', fontSize: '0.78rem', padding: '2rem' }}>
            No events yet
          </div>
        )}
        {recentEvents.map((ev, i) => {
          const color = SEV_COLOR[ev.severity] ?? '#9ca3af'
          const icon = TYPE_ICON[ev.event_type] ?? '•'
          const ts = new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          return (
            <div
              key={i}
              className="anim-fade-in"
              style={{
                padding: '5px 1rem', borderBottom: '1px solid var(--cr-border)',
                borderLeft: `3px solid ${color}`,
                background: i === 0 ? `${color}08` : 'transparent',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                <span style={{ fontSize: '0.72rem' }}>{icon}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--cr-text-muted)', fontFamily: 'monospace' }}>{ts}</span>
                <span style={{
                  fontSize: '0.62rem', padding: '1px 5px', borderRadius: '3px',
                  background: `${color}22`, color,
                }}>
                  {ev.severity}
                </span>
                {ev.connector_id && (
                  <span style={{ fontSize: '0.62rem', color: 'var(--cr-accent)', padding: '1px 5px',
                    borderRadius: '3px', background: 'rgba(0,212,255,0.1)' }}>
                    C{ev.connector_id}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--cr-text)', lineHeight: 1.3, wordBreak: 'break-word' }}>
                {ev.message}
              </div>
              {ev.topic && (
                <div style={{ fontSize: '0.65rem', color: 'var(--cr-text-muted)', marginTop: '1px', fontFamily: 'monospace' }}>
                  {ev.topic}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
