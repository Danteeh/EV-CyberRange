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
  
  // ── Attack State ──────────────────────────────────────────
  activeAttacks: {}, // { "target:port": { cve, severity, startTime } }
  attackEvents: [],
  
  // ── Infrastructure Impact State ───────────────────────────
  // Tracks how attacks propagate to EV, EVSE, CSMS
  infrastructureImpact: {
    ev: null,      // { cve, impact, severity }
    evse: null,
    csms: null,
  },
  
  // ── Topology State (persisted) ────────────────────────────
  topologyNodes: null, // Will be initialized on first load
  topologyEdges: null,
  
  setTopologyNodes: (nodes) => set({ topologyNodes: nodes }),
  setTopologyEdges: (edges) => set({ topologyEdges: edges }),
  resetTopology: () => set({ topologyNodes: null, topologyEdges: null }),
  
  // ── UI ────────────────────────────────────────────────────
  selectedConnector: 1,
  activePanel: 'control',

  // ── Polling para verificar servicios ──────────────────────
  _pollInterval: null,
  _attackFeedSource: null,

  startPolling() {
    const existing = get()._pollInterval
    if (existing) clearInterval(existing)

    // Initial check
    get().checkServices()

    // Poll every 5 seconds
    const interval = setInterval(() => get().checkServices(), 5000)
    set({ _pollInterval: interval })
    
    // Start attack feed SSE
    get().connectAttackFeed()
  },

  stopPolling() {
    const interval = get()._pollInterval
    if (interval) {
      clearInterval(interval)
      set({ _pollInterval: null })
    }
    
    const eventSource = get()._attackFeedSource
    if (eventSource) {
      eventSource.close()
      set({ _attackFeedSource: null })
    }
  },

  connectAttackFeed() {
    const existing = get()._attackFeedSource
    if (existing) existing.close()
    
    try {
      const eventSource = new EventSource('/api/attack-feed/stream')
      
      eventSource.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          get().processAttackEvent(event)
        } catch (err) {
          console.error('[AttackFeed] Failed to parse:', err)
        }
      }
      
      eventSource.onerror = (err) => {
        console.error('[AttackFeed] SSE error, reconnecting in 3s...', err)
        eventSource.close()
        setTimeout(() => get().connectAttackFeed(), 3000)
      }
      
      set({ _attackFeedSource: eventSource })
    } catch (err) {
      console.error('[AttackFeed] Failed to connect:', err)
    }
  },
  
  processAttackEvent(event) {
    const { activeAttacks, attackEvents } = get()
    const target = event.target
    
    // Add to events list
    const newEvents = [...attackEvents, { ...event, id: Date.now() + Math.random() }].slice(-100)
    
    // Update active attacks based on event type
    const newActiveAttacks = { ...activeAttacks }
    
    // Impact mapping: which CVE affects which infrastructure
    const impactMap = {
      'CVE-2024-11665': { // Hardy Barth RCE
        evse: 'RCE - Charging parameters manipulated',
        ev: 'Session hijacked - billing fraud risk',
        csms: 'Credentials exposed - lateral movement possible'
      },
      'CVE-2024-11666': { // Hardy Barth Credential Exposure
        evse: 'Credentials leaked',
        ev: null,
        csms: 'MQTT credentials compromised'
      },
      'CVE-2018-7800': { // Schneider Hard-coded Creds
        evse: 'Admin access - full control',
        ev: 'Charging manipulation possible',
        csms: 'Backend credentials at risk'
      },
      'CVE-2023-32249': { // Wallbox Unauth API
        evse: 'API exposed - config readable',
        ev: 'Session data accessible',
        csms: 'WiFi credentials leaked'
      },
      'CVE-2022-26132': { // ChargePoint DoS
        evse: 'Service disrupted - DoS',
        ev: 'Charging interrupted',
        csms: 'Connectivity lost'
      },
      'CVE-2024-43659': { // ABB Credential Exposure
        evse: 'OCPP credentials exposed',
        ev: null,
        csms: 'Backend compromise possible'
      },
      'CVE-2025-12357': { // ISO 15118 MITM
        evse: 'TLS intercepted',
        ev: 'Plug&Charge credentials stolen',
        csms: 'Authentication bypassed'
      }
    }
    
    if (event.type === 'attack_start') {
      newActiveAttacks[target] = {
        cve: event.cve,
        severity: event.severity,
        name: event.name,
        startTime: event.timestamp,
        attack_type: event.attack_type
      }
      
      // Calculate infrastructure impact
      const impacts = impactMap[event.cve] || {}
      set({
        infrastructureImpact: {
          ev: impacts.ev ? { cve: event.cve, impact: impacts.ev, severity: event.severity } : null,
          evse: impacts.evse ? { cve: event.cve, impact: impacts.evse, severity: event.severity } : null,
          csms: impacts.csms ? { cve: event.cve, impact: impacts.csms, severity: event.severity } : null,
        }
      })
    } else if (event.type === 'attack_success' || event.type === 'attack_failure') {
      // Keep attack visible for 10 seconds after completion
      if (newActiveAttacks[target]) {
        newActiveAttacks[target].completed = true
        newActiveAttacks[target].success = event.type === 'attack_success'
        
        // Clear infrastructure impact after delay
        setTimeout(() => {
          const current = get().activeAttacks
          const updated = { ...current }
          delete updated[target]
          set({ 
            activeAttacks: updated,
            infrastructureImpact: { ev: null, evse: null, csms: null }
          })
        }, 10000)
      }
    }
    
    set({ 
      attackEvents: newEvents,
      activeAttacks: newActiveAttacks
    })
  },
  
  isUnderAttack(target) {
    const { activeAttacks } = get()
    return activeAttacks[target] || null
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
