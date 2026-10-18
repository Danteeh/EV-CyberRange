import { useStore } from '../store'

const STATE_COLOR = {
  Charging:      '#10b981',
  Available:     '#00d4ff',
  Preparing:     '#f59e0b',
  SuspendedEV:   '#f59e0b',
  SuspendedEVSE: '#f59e0b',
  Finishing:     '#a78bfa',
  Faulted:       '#ef4444',
  Unavailable:   '#6b7280',
  UNKNOWN:       '#4b5563',
  // Estados internos de EVerest
  Unplugged:                  '#6b7280',
  WaitingForAuthentication:   '#f59e0b',
  TransactionStarted:         '#10b981',
  TransactionFinished:        '#a78bfa',
}
function sc(s) { return STATE_COLOR[s] ?? '#4b5563' }

// Isometric cube: cx,cy = SVG center of top face, w=half-width, h=height, d=depth
// Uses fixed isometric angles (30 deg) with explicit face polygons
function IsoCube({ cx, cy, w, h, d, fill, stroke = '#1e293b' }) {
  // Top face corners (rhombus)
  const tTop   = `${cx},${cy}`
  const tRight = `${cx + w},${cy + w * 0.5}`
  const tBot   = `${cx},${cy + w}`
  const tLeft  = `${cx - w},${cy + w * 0.5}`

  // Bottom of left face (drop by h)
  const bLeft  = `${cx - w},${cy + w * 0.5 + h}`
  const bBot   = `${cx},${cy + w + h}`
  // Bottom of right face
  const bRight = `${cx + w},${cy + w * 0.5 + h}`

  const top   = `${tTop} ${tRight} ${tBot} ${tLeft}`
  const left  = `${tLeft} ${tBot} ${bBot} ${bLeft}`
  const right = `${tRight} ${tBot} ${bBot} ${bRight}`

  const topFill   = lighten(fill, 1.25)
  const leftFill  = darken(fill, 0.55)
  const rightFill = darken(fill, 0.75)

  return (
    <g>
      <polygon points={left}  fill={leftFill}  stroke={stroke} strokeWidth={0.5} />
      <polygon points={right} fill={rightFill} stroke={stroke} strokeWidth={0.5} />
      <polygon points={top}   fill={topFill}   stroke={stroke} strokeWidth={0.5} />
    </g>
  )
}

function lighten(hex, factor) {
  return adjustBrightness(hex, factor)
}
function darken(hex, factor) {
  return adjustBrightness(hex, factor)
}
function adjustBrightness(hex, factor) {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h.split('').map(c => c + c).join('')
  const r = Math.min(255, Math.round(parseInt(h.slice(0,2),16) * factor))
  const g = Math.min(255, Math.round(parseInt(h.slice(2,4),16) * factor))
  const b = Math.min(255, Math.round(parseInt(h.slice(4,6),16) * factor))
  return `rgb(${r},${g},${b})`
}

// Animated cable between two SVG points
function Cable({ x1, y1, x2, y2, active, color }) {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2 + 8
  const d = `M${x1},${y1} Q${mx},${my} ${x2},${y2}`
  return (
    <g>
      <path d={d} fill="none" stroke="#374151" strokeWidth={2.5} />
      {active && (
        <path d={d} fill="none" stroke={color} strokeWidth={2}
              strokeLinecap="round" className="anim-flow"
              style={{ strokeDasharray: '8 5' }} />
      )}
    </g>
  )
}

// EV vehicle block at SVG position cx,cy
function EVBlock({ cx, cy, id, data }) {
  const state = data?.state ?? 'UNKNOWN'
  const charging = state === 'Charging'
  const bodyColor = charging ? '#1d4ed8' : '#1e3a5f'
  const roofColor = charging ? '#2563eb' : '#1e40af'

  return (
    <g>
      {/* Wheels */}
      <IsoCube cx={cx - 14} cy={cy + 16} w={6}  h={5}  d={6}  fill="#111827" />
      <IsoCube cx={cx + 14} cy={cy + 16} w={6}  h={5}  d={6}  fill="#111827" />
      {/* Body */}
      <IsoCube cx={cx}      cy={cy + 4}  w={20} h={14} d={22} fill={bodyColor} />
      {/* Roof */}
      <IsoCube cx={cx}      cy={cy}      w={14} h={10} d={16} fill={roofColor} />
      {/* Label */}
      <text x={cx} y={cy - 10} textAnchor="middle" fontSize={9} fontWeight="600"
            fill={charging ? '#10b981' : '#9ca3af'} fontFamily="monospace">
        EV-{String(id).padStart(2,'0')}
      </text>
      {charging && (
        <text x={cx} y={cy - 20} textAnchor="middle" fontSize={7.5}
              fill="#10b981" fontFamily="monospace" className="anim-pulse-dot">
          CHARGING
        </text>
      )}
    </g>
  )
}

// EVSE charger block
function EVSEBlock({ cx, cy, id, data, hasAttack }) {
  const state = data?.state ?? 'UNKNOWN'
  const charging = state === 'Charging'
  const color = hasAttack ? '#ef4444' : sc(state)
  const power = data?.metrics?.power_w ?? 0
  const energy = (data?.metrics?.energy_wh ?? 0) / 1000

  return (
    <g className={hasAttack ? 'anim-attack' : charging ? 'anim-charge' : ''}>
      {/* Base */}
      <IsoCube cx={cx}  cy={cy + 28} w={14} h={6}  d={14} fill="#374151" />
      {/* Body */}
      <IsoCube cx={cx}  cy={cy + 4}  w={13} h={28} d={12} fill={color} />
      {/* Screen */}
      <IsoCube cx={cx}  cy={cy + 6}  w={7}  h={4}  d={4}  fill={charging ? '#10b981' : '#1f2937'} />

      <text x={cx} y={cy - 8} textAnchor="middle" fontSize={9} fontWeight="700"
            fill={color} fontFamily="monospace">
        EVSE-{id}
      </text>
      <text x={cx} y={cy + 1} textAnchor="middle" fontSize={7.5}
            fill="#9ca3af" fontFamily="monospace">
        {state}
      </text>
      {charging && (
        <>
          <text x={cx} y={cy - 18} textAnchor="middle" fontSize={8}
                fill="#10b981" fontFamily="monospace">
            {power.toFixed(0)}W
          </text>
          <text x={cx} y={cy - 28} textAnchor="middle" fontSize={8}
                fill="#00d4ff" fontFamily="monospace">
            {energy.toFixed(2)}kWh
          </text>
        </>
      )}
    </g>
  )
}

// SteVe server block
function SteVeBlock({ cx, cy, ocppStatus }) {
  const ok = ocppStatus === 'CONNECTED'
  const color = ok ? '#1e3a5f' : '#374151'

  return (
    <g className={ok ? 'anim-charge' : ''}>
      {/* Server tower */}
      <IsoCube cx={cx} cy={cy}      w={16} h={50} d={18} fill={color} />
      {/* LED indicators */}
      {[0,1,2,3].map(i => (
        <IsoCube key={i} cx={cx - 6} cy={cy + 4 + i * 8} w={3} h={3} d={2}
                 fill={ok ? '#10b981' : '#ef4444'} />
      ))}

      <text x={cx} y={cy - 10} textAnchor="middle" fontSize={10} fontWeight="700"
            fill={ok ? '#00d4ff' : '#9ca3af'} fontFamily="monospace">
        SteVe
      </text>
      <text x={cx} y={cy + 1} textAnchor="middle" fontSize={7.5}
            fill={ok ? '#10b981' : '#ef4444'} fontFamily="monospace">
        {ok ? 'ONLINE' : 'OFFLINE'}
      </text>
    </g>
  )
}

export default function TopologyView() {
  const { connectors, connectivity, attacks } = useStore()

  const c1 = connectors?.['1']
  const c2 = connectors?.['2']
  const ocpp = connectivity?.ocpp ?? 'UNKNOWN'
  const ocppOk = ocpp === 'CONNECTED'
  const c1charging = c1?.state === 'Charging'
  const c2charging = c2?.state === 'Charging'
  const hasAttack1 = attacks?.some(a => a.status === 'RUNNING' && (!a.connector_id || a.connector_id === 1))
  const hasAttack2 = attacks?.some(a => a.status === 'RUNNING' && a.connector_id === 2)
  const anyAttack  = attacks?.some(a => a.status === 'RUNNING')

  // Layout positions (SVG coordinates, viewBox 900x460)
  // Left side: EV1 + EVSE1, Right side: EV2 + EVSE2, Center-right: SteVe
  const EV1   = { cx: 120, cy: 260 }
  const EVSE1 = { cx: 260, cy: 220 }
  const EV2   = { cx: 380, cy: 190 }
  const EVSE2 = { cx: 490, cy: 160 }
  const STEVE = { cx: 660, cy: 200 }

  // Cable anchor points (bottom of EVSE top-face, approximate)
  const e1Cable = { x: EVSE1.cx + 13, y: EVSE1.cy + 20 }
  const e2Cable = { x: EVSE2.cx + 13, y: EVSE2.cy + 18 }
  const steveIn = { x: STEVE.cx - 16, y: STEVE.cy + 30 }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <svg
        width="100%" height="100%"
        viewBox="0 0 900 460"
        preserveAspectRatio="xMidYMid meet"
        style={{ position: 'absolute', inset: 0 }}
      >
        <defs>
          <pattern id="iso-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M40 0 L0 0 0 40" fill="none" stroke="#1a2030" strokeWidth="0.8" />
          </pattern>
          <filter id="glow-green">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Background */}
        <rect width="900" height="460" fill="#0a0e1a" />
        <rect width="900" height="460" fill="url(#iso-grid)" />

        {/* Isometric floor tiles to give depth */}
        {/* Row of floor diamonds */}
        {[-1,0,1,2,3,4].map(col =>
          [0,1,2,3].map(row => {
            const tx = 80 + col * 80 + row * 40
            const ty = 320 + row * 20 - col * 20
            const pts = `${tx},${ty} ${tx+40},${ty+20} ${tx},${ty+40} ${tx-40},${ty+20}`
            return <polygon key={`${col}-${row}`} points={pts}
              fill={((col+row)%2===0) ? '#0d1220' : '#0f1525'} stroke="#1a2535" strokeWidth="0.5" />
          })
        )}

        {/* Cables — rendered under blocks */}
        <Cable x1={EV1.cx + 18}   y1={EV1.cy + 22}
               x2={e1Cable.x - 13} y2={e1Cable.y}
               active={c1charging} color="#10b981" />

        <Cable x1={EV2.cx + 18}   y1={EV2.cy + 22}
               x2={e2Cable.x - 13} y2={e2Cable.y}
               active={c2charging} color="#10b981" />

        <Cable x1={e1Cable.x} y1={e1Cable.y}
               x2={steveIn.x} y2={steveIn.y}
               active={ocppOk} color="#00d4ff" />

        <Cable x1={e2Cable.x} y1={e2Cable.y}
               x2={steveIn.x} y2={steveIn.y - 20}
               active={ocppOk} color="#00d4ff" />

        {/* EV blocks */}
        <EVBlock cx={EV1.cx} cy={EV1.cy} id={1} data={c1} />
        <EVBlock cx={EV2.cx} cy={EV2.cy} id={2} data={c2} />

        {/* EVSE blocks */}
        <EVSEBlock cx={EVSE1.cx} cy={EVSE1.cy} id={1} data={c1} hasAttack={hasAttack1} />
        <EVSEBlock cx={EVSE2.cx} cy={EVSE2.cy} id={2} data={c2} hasAttack={hasAttack2} />

        {/* SteVe server */}
        <SteVeBlock cx={STEVE.cx} cy={STEVE.cy} ocppStatus={ocpp} />

        {/* OCPP protocol label on the wire */}
        <text x="570" y="165" textAnchor="middle" fontSize={8} fill="#00d4ff88" fontFamily="monospace">
          OCPP 1.6J
        </text>

        {/* Status badges top-left */}
        <g>
          <rect x="10" y="10" width="96" height="22" rx="3"
                fill="#111827" stroke="#374151" strokeWidth="1" />
          <circle cx="22" cy="21" r="4"
                  fill={connectivity?.mqtt ? '#10b981' : '#ef4444'}
                  className={connectivity?.mqtt ? 'anim-pulse-dot' : ''} />
          <text x="30" y="25" fontSize={9} fill="#9ca3af" fontFamily="monospace">
            MQTT {connectivity?.mqtt ? 'OK' : 'OFFLINE'}
          </text>
        </g>

        {anyAttack && (
          <g>
            <rect x="10" y="38" width="130" height="22" rx="3"
                  fill="#450a0a" stroke="#ef4444" strokeWidth="1" />
            <text x="20" y="53" fontSize={9} fill="#ef4444" fontFamily="monospace" className="anim-pulse-dot">
              ATTACK IN PROGRESS
            </text>
          </g>
        )}

        {/* Legend */}
        <g transform="translate(10, 400)">
          {[
            { color: '#10b981', label: 'Charging' },
            { color: '#00d4ff', label: 'Available' },
            { color: '#f59e0b', label: 'Suspended' },
            { color: '#ef4444', label: 'Faulted' },
          ].map(({ color, label }, i) => (
            <g key={label} transform={`translate(${i * 110}, 0)`}>
              <rect width={10} height={10} rx={2} fill={color} y={-8} />
              <text x={14} y={1} fontSize={8} fill="#6b7280" fontFamily="monospace">{label}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  )
}
