import { useState } from 'react'
import { useStore } from '../store'
import { Plug, PlugZap, Pause, Play, Zap, CreditCard } from 'lucide-react'

const BTN = ({ onClick, color = 'var(--cr-accent)', icon: Icon, label, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      display: 'flex', alignItems: 'center', gap: '6px',
      padding: '7px 12px', borderRadius: '6px', border: `1px solid ${color}`,
      background: 'transparent', color, cursor: disabled ? 'not-allowed' : 'pointer',
      fontSize: '0.78rem', fontFamily: 'monospace', opacity: disabled ? 0.4 : 1,
      transition: 'background 0.15s',
      width: '100%', justifyContent: 'center',
    }}
    onMouseEnter={e => !disabled && (e.currentTarget.style.background = `${color}22`)}
    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
  >
    {Icon && <Icon size={14} />}
    {label}
  </button>
)

const SIMULATIONS = [
  { label: 'AC 3ph 16A', value: 'sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 16,3;sleep 36000#unplug#pause;sleep 3600#draw_power_regulated 16,3;sleep 36000' },
  { label: 'AC 1ph 32A', value: 'sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 32,1;sleep 36000#unplug#pause;sleep 3600#draw_power_regulated 32,1;sleep 36000' },
  { label: 'AC Diode Fail', value: 'sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 32,3;sleep 5;diode_fail;sleep 36000#unplug' },
  { label: 'AC Error E', value: 'sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 16,3;sleep 3;error_e;sleep 36000#unplug' },
  { label: 'AC RCD Error', value: 'sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 16,3;sleep 3;rcd_current 10.5;sleep 5;rcd_current 0.2;sleep 36000#unplug' },
]

export default function ControlPanel() {
  const { selectedConnector, setSelectedConnector, connectors, sendControl } = useStore()
  const [simulation, setSimulation] = useState(SIMULATIONS[0].value)
  const [idTag, setIdTag] = useState('CARD-001')
  const [maxCurrent, setMaxCurrent] = useState(16)
  const [busy, setBusy] = useState(false)

  const c = connectors?.[String(selectedConnector)]
  const state = c?.state ?? 'UNKNOWN'
  const isCharging = state === 'Charging'
  const isPaused = ['SuspendedEV', 'SuspendedEVSE'].includes(state)

  async function cmd(action, body = {}) {
    setBusy(true)
    try { await sendControl(selectedConnector, action, body) }
    finally { setBusy(false) }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem' }}>

      {/* Selector de conector */}
      <div>
        <label style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', display: 'block', marginBottom: '4px' }}>
          CONNECTOR
        </label>
        <div style={{ display: 'flex', gap: '6px' }}>
          {[1, 2].map(id => (
            <button
              key={id}
              onClick={() => setSelectedConnector(id)}
              style={{
                flex: 1, padding: '6px', borderRadius: '6px', fontFamily: 'monospace',
                fontSize: '0.8rem', cursor: 'pointer',
                border: `1px solid ${selectedConnector === id ? 'var(--cr-accent)' : 'var(--cr-border)'}`,
                background: selectedConnector === id ? 'rgba(0,212,255,0.1)' : 'transparent',
                color: selectedConnector === id ? 'var(--cr-accent)' : 'var(--cr-text-muted)',
              }}
            >
              EVSE-{id}
            </button>
          ))}
        </div>
      </div>

      {/* Estado actual */}
      <div style={{
        padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--cr-border)',
        background: 'var(--cr-surface2)', fontSize: '0.78rem',
      }}>
        <span style={{ color: 'var(--cr-text-muted)' }}>STATE: </span>
        <span style={{ color: stateColor(state), fontWeight: 700 }}>{state}</span>
        {c?.metrics && (
          <div style={{ marginTop: '6px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
            <Metric label="Power" value={`${(c.metrics.power_w ?? 0).toFixed(0)} W`} />
            <Metric label="Energy" value={`${((c.metrics.energy_wh ?? 0)/1000).toFixed(2)} kWh`} />
            <Metric label="Voltage" value={`${(c.metrics.voltage_l1_v ?? 0).toFixed(0)} V`} />
            <Metric label="Current" value={`${(c.metrics.current_l1_a ?? 0).toFixed(1)} A`} />
          </div>
        )}
      </div>

      {/* Simulación */}
      <div>
        <label style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', display: 'block', marginBottom: '4px' }}>
          SIMULATION PROFILE
        </label>
        <select
          value={simulation}
          onChange={e => setSimulation(e.target.value)}
          style={{
            width: '100%', padding: '6px 8px', borderRadius: '6px',
            background: 'var(--cr-surface2)', border: '1px solid var(--cr-border)',
            color: 'var(--cr-text)', fontFamily: 'monospace', fontSize: '0.78rem', cursor: 'pointer',
          }}
        >
          {SIMULATIONS.map(s => <option key={s.label} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      {/* Botones principales */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <BTN icon={PlugZap} label="CAR PLUGIN" color="var(--cr-green)" disabled={busy || isCharging}
             onClick={() => cmd('plugin', { simulation, id_tag: idTag })} />
        <BTN icon={Plug} label="STOP & UNPLUG" color="var(--cr-red)" disabled={busy || (!isCharging && !isPaused)}
             onClick={() => cmd('unplug')} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          <BTN icon={Pause} label="PAUSE" color="var(--cr-yellow)" disabled={busy || !isCharging}
               onClick={() => cmd('pause')} />
          <BTN icon={Play}  label="RESUME" color="var(--cr-green)" disabled={busy || !isPaused}
               onClick={() => cmd('resume')} />
        </div>
      </div>

      {/* RFID auth */}
      <div>
        <label style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', display: 'block', marginBottom: '4px' }}>
          RFID ID TAG
        </label>
        <div style={{ display: 'flex', gap: '6px' }}>
          <input
            value={idTag}
            onChange={e => setIdTag(e.target.value)}
            style={{
              flex: 1, padding: '6px 8px', borderRadius: '6px',
              background: 'var(--cr-surface2)', border: '1px solid var(--cr-border)',
              color: 'var(--cr-text)', fontFamily: 'monospace', fontSize: '0.78rem',
            }}
          />
          <button
            onClick={() => cmd('authorize', { id_tag: idTag })}
            disabled={busy}
            style={{
              padding: '6px 10px', borderRadius: '6px',
              background: 'rgba(124,58,237,0.2)', border: '1px solid var(--cr-accent2)',
              color: 'var(--cr-accent2)', cursor: 'pointer', fontSize: '0.78rem', fontFamily: 'monospace',
            }}
          >
            <CreditCard size={14} />
          </button>
        </div>
      </div>

      {/* Corriente máxima */}
      <div>
        <label style={{ fontSize: '0.7rem', color: 'var(--cr-text-muted)', display: 'block', marginBottom: '4px' }}>
          MAX CURRENT: {maxCurrent}A
        </label>
        <input
          type="range" min={6} max={32} step={2} value={maxCurrent}
          onChange={e => setMaxCurrent(Number(e.target.value))}
          onMouseUp={() => cmd('set_max_current', { amperes: maxCurrent })}
          style={{ width: '100%', accentColor: 'var(--cr-accent)' }}
        />
      </div>

    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div>
      <span style={{ color: 'var(--cr-text-muted)', fontSize: '0.68rem' }}>{label}: </span>
      <span style={{ color: 'var(--cr-accent)', fontSize: '0.78rem', fontWeight: 600 }}>{value}</span>
    </div>
  )
}

const STATE_COLOR = {
  Charging: '#10b981', Available: '#00d4ff', Preparing: '#f59e0b',
  SuspendedEV: '#f59e0b', SuspendedEVSE: '#f59e0b', Finishing: '#a78bfa',
  Faulted: '#ef4444', Unavailable: '#6b7280', UNKNOWN: '#4b5563',
  // Estados internos de EVerest
  Unplugged: '#6b7280', WaitingForAuthentication: '#f59e0b',
  TransactionStarted: '#10b981', TransactionFinished: '#a78bfa',
}
function stateColor(s) { return STATE_COLOR[s] ?? '#4b5563' }
