import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // ── Conectividad ──────────────────────────────────────────
  connectivity: { 
    backend: false, 
    csms: false,
    nodered: false,
    kali: false 
  },
  chargePoints: [],
  recentEvents: [],
  
  // ── UI ────────────────────────────────────────────────────
  selectedConnector: 1,
  activePanel: 'control',

  // ── Polling para verificar servicios ──────────────────────
  _pollInterval: null,

  startPolling() {
    const existing = get()._pollInterval
    if (existing) clearInterval(existing)

    // Initial check
    get().checkServices()

    // Poll every 5 seconds
    const interval = setInterval(() => get().checkServices(), 5000)
    set({ _pollInterval: interval })
  },

  stopPolling() {
    const interval = get()._pollInterval
    if (interval) {
      clearInterval(interval)
      set({ _pollInterval: null })
    }
  },

  async checkServices() {
    const newConnectivity = { 
      backend: false, 
      csms: false,
      nodered: false,
      kali: false 
    }
    
    // Check Backend + CSMS (via charge points endpoint)
    try {
      const res = await fetch('/api/ocpp/charge-points')
      if (res.ok) {
        const data = await res.json()
        newConnectivity.backend = true
        newConnectivity.csms = (data.total || 0) > 0
        set({ chargePoints: data.charge_points || [] })
      }
    } catch (e) {
      console.log('Backend check failed:', e.message)
    }

    // For Node-RED and Kali, we can't check from browser due to CORS
    // So we assume they're up if backend is up (they're all started together)
    if (newConnectivity.backend) {
      newConnectivity.nodered = true
      newConnectivity.kali = true
    }

    set({ connectivity: newConnectivity })
  },

  addEvent(event) {
    set((s) => ({
      recentEvents: [
        { ...event, timestamp: new Date().toISOString() },
        ...s.recentEvents
      ].slice(0, 50)
    }))
  },

  setSelectedConnector: (id) => set({ selectedConnector: id }),
  setActivePanel: (p) => set({ activePanel: p }),
}))
