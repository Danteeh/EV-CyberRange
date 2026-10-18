import { create } from 'zustand'

// WS conecta siempre directo al backend (puerto 8000).
// El proxy de Vite no se usa para WS — causa ECONNABORTED con uvicorn.
// En produccion (backend sirve el build estatico) se usa la misma host/port.
const WS_URL = (() => {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  // En dev (5173) conectar directo a 8000. En prod el host ya es el backend.
  const host = window.location.port === '5173'
    ? `${window.location.hostname}:8000`
    : window.location.host
  return `${proto}//${host}/ws/realtime`
})()

export const useStore = create((set, get) => ({
  // ── Conectividad ──────────────────────────────────────────
  wsConnected: false,
  station: null,
  connectivity: { mqtt: false, ocpp: 'UNKNOWN' },
  connectors: {},
  attacks: [],
  recentEvents: [],
  updatedAt: null,

  // ── UI ────────────────────────────────────────────────────
  selectedConnector: 1,
  activePanel: 'control',   // 'control' | 'events' | 'attacks'
  attackScenarios: [],

  // ── WebSocket ─────────────────────────────────────────────
  _ws: null,

  connectWS() {
    const existing = get()._ws
    if (existing) existing.close()

    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      set({ wsConnected: true })
      console.log('[WS] connected')
    }
    ws.onclose = () => {
      set({ wsConnected: false })
      console.log('[WS] disconnected — retry in 3s')
      setTimeout(() => get().connectWS(), 3000)
    }
    ws.onerror = (e) => console.error('[WS] error', e)

    ws.onmessage = ({ data }) => {
      try {
        const msg = JSON.parse(data)
        if (msg.type === 'state') {
          set({
            station: msg.station,
            connectivity: msg.connectivity,
            connectors: msg.connectors,
            attacks: msg.attacks,
            recentEvents: msg.recent_events,
            updatedAt: msg.updated_at,
          })
        } else if (msg.type === 'event') {
          set((s) => ({
            recentEvents: [msg.event, ...s.recentEvents].slice(0, 100),
          }))
        }
      } catch (e) {
        console.error('[WS] parse error', e)
      }
    }

    set({ _ws: ws })
  },

  setSelectedConnector: (id) => set({ selectedConnector: id }),
  setActivePanel: (p) => set({ activePanel: p }),

  // ── Carga escenarios de ataque ────────────────────────────
  async loadScenarios() {
    try {
      const r = await fetch('/api/attacks/scenarios')
      const d = await r.json()
      set({ attackScenarios: d.scenarios })
    } catch (e) {
      console.error('loadScenarios', e)
    }
  },

  // ── Control API ───────────────────────────────────────────
  async sendControl(connectorId, action, body = {}) {
    const r = await fetch(`/api/control/connector/${connectorId}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    return r.json()
  },

  async startAttack(scenarioId) {
    const r = await fetch(`/api/attacks/${scenarioId}/start`, { method: 'POST' })
    return r.json()
  },

  async stopAttack(scenarioId) {
    const r = await fetch(`/api/attacks/${scenarioId}/stop`, { method: 'POST' })
    return r.json()
  },
}))
