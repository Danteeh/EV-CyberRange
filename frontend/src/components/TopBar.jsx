import { useStore } from '../store'
import { Wifi, WifiOff, Shield, Activity } from 'lucide-react'

export default function TopBar() {
  const { wsConnected, connectivity, station, updatedAt } = useStore()

  const ocppOk = connectivity?.ocpp === 'CONNECTED'
  const mqttOk = connectivity?.mqtt === true

  const ts = updatedAt ? new Date(updatedAt).toLocaleTimeString() : '--:--:--'

  return (
    <header
      style={{
        background: 'var(--cr-surface)',
        borderBottom: '1px solid var(--cr-border)',
        padding: '0 1.25rem',
        height: '48px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
        zIndex: 50,
      }}
    >
      {/* Left: logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <Shield size={20} color="var(--cr-accent)" />
        <span style={{ color: 'var(--cr-accent)', fontWeight: 700, fontSize: '0.95rem', letterSpacing: '0.08em' }}>
          EV-CYBERRANGE
        </span>
        {station && (
          <span style={{ color: 'var(--cr-text-muted)', fontSize: '0.75rem', marginLeft: '0.5rem' }}>
            {station.id} · {station.protocol}
          </span>
        )}
      </div>

      {/* Right: status badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <StatusBadge label="WS" ok={wsConnected} icon={wsConnected ? Wifi : WifiOff} />
        <StatusBadge label="MQTT" ok={mqttOk} />
        <StatusBadge label="OCPP" ok={ocppOk} />
        <span style={{ color: 'var(--cr-text-muted)', fontSize: '0.7rem' }}>
          <Activity size={12} style={{ display: 'inline', marginRight: '4px' }} />
          {ts}
        </span>
      </div>
    </header>
  )
}

function StatusBadge({ label, ok, icon: Icon }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem' }}>
      {Icon && <Icon size={13} color={ok ? 'var(--cr-green)' : 'var(--cr-red)'} />}
      {!Icon && (
        <span
          className={ok ? 'anim-pulse-dot' : ''}
          style={{
            width: 7, height: 7, borderRadius: '50%',
            background: ok ? 'var(--cr-green)' : 'var(--cr-red)',
            display: 'inline-block',
          }}
        />
      )}
      <span style={{ color: ok ? 'var(--cr-green)' : 'var(--cr-red)', fontWeight: 600 }}>
        {label}
      </span>
    </div>
  )
}
