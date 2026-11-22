import { useCallback, useMemo, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '../store'
import { 
  Car, 
  Wifi, 
  WifiOff, 
  Zap, 
  Server, 
  ShieldAlert,
  PlugZap,
  Activity,
  AlertTriangle,
  Battery,
  BatteryCharging,
  Skull,
  Crosshair
} from 'lucide-react'

// ═══════════════════════════════════════════════════════════
// Custom Node Types - Electric Amber Theme with Pro Icons
// ═══════════════════════════════════════════════════════════

function EVNode({ data, selected }) {
  const isCharging = data.state === 'Charging'
  const impact = useStore((state) => state.infrastructureImpact.ev)
  const isAffected = !!impact
  
  return (
    <div className={`ev-node-3d ${isCharging ? 'charging' : ''} ${selected ? 'selected' : ''} ${isAffected ? 'affected' : ''}`}>
      <Handle type="source" position={Position.Right} id="out" className="handle-amber" />
      
      {/* Glow effect behind */}
      {isCharging && !isAffected && <div className="ev-glow" />}
      {isAffected && <div className="ev-attack-glow" />}
      
      <div className="ev-icon-container">
        <Car 
          size={56} 
          strokeWidth={1.5}
          className={`ev-icon ${isCharging ? 'charging' : ''} ${isAffected ? 'affected' : ''}`}
        />
        {isCharging && !isAffected && (
          <div className="charging-indicator">
            <BatteryCharging size={18} className="battery-pulse" />
          </div>
        )}
        {isAffected && (
          <div className="attack-indicator">
            <AlertTriangle size={18} className="alert-pulse" />
          </div>
        )}
      </div>
      
      <div className="ev-info">
        <span className="ev-label">{data.label}</span>
        {isAffected ? (
          <>
            <span className="ev-status affected">
              <AlertTriangle size={10} /> IMPACTED
            </span>
            <div className="impact-details">
              <span className="impact-cve">{impact.cve}</span>
              <span className="impact-text">{impact.impact}</span>
            </div>
          </>
        ) : (
          <span className={`ev-status ${isCharging ? 'charging' : 'idle'}`}>
            {isCharging ? 'Charging' : 'Idle'}
          </span>
        )}
      </div>
      
      <style>{`
        .ev-node-3d {
          padding: 16px;
          background: linear-gradient(145deg, #1c1e22 0%, #141518 100%);
          border: 2px solid #3a3d44;
          border-radius: 16px;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.03) inset;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          min-width: 100px;
        }
        .ev-node-3d:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            0 0 20px rgba(245, 158, 11, 0.1);
          border-color: #4a4e58;
        }
        .ev-node-3d.selected {
          border-color: #f59e0b;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 30px rgba(245, 158, 11, 0.2);
        }
        .ev-node-3d.charging {
          border-color: #22c55e;
        }
        .ev-node-3d.affected {
          border-color: #ef4444;
          animation: affected-pulse 1s ease-in-out infinite;
        }
        .ev-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 120px;
          height: 120px;
          background: radial-gradient(circle, rgba(34, 197, 94, 0.2) 0%, transparent 70%);
          border-radius: 50%;
          animation: pulse-glow 2s ease-in-out infinite;
          pointer-events: none;
        }
        .ev-attack-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 140px;
          height: 140px;
          background: radial-gradient(circle, rgba(239, 68, 68, 0.3) 0%, transparent 70%);
          border-radius: 50%;
          animation: attack-glow 0.8s ease-in-out infinite;
          pointer-events: none;
        }
        .ev-icon-container {
          display: flex;
          justify-content: center;
          align-items: center;
          position: relative;
          margin-bottom: 8px;
        }
        .ev-icon {
          color: #71717a;
          transition: all 0.3s;
        }
        .ev-icon.charging {
          color: #22c55e;
          filter: drop-shadow(0 0 8px rgba(34, 197, 94, 0.5));
        }
        .ev-icon.affected {
          color: #ef4444;
          filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
          animation: icon-shake 0.3s ease-in-out infinite;
        }
        .charging-indicator {
          position: absolute;
          top: -4px;
          right: -4px;
          background: #22c55e;
          border-radius: 50%;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .attack-indicator {
          position: absolute;
          top: -4px;
          right: -4px;
          background: #ef4444;
          border-radius: 50%;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: indicator-pulse 0.5s ease-in-out infinite;
        }
        .battery-pulse {
          color: white;
          animation: pulse-subtle 1.5s ease-in-out infinite;
        }
        .alert-pulse {
          color: white;
          animation: pulse-fast 0.5s ease-in-out infinite;
        }
        .ev-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
        }
        .ev-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: #f4f4f5;
        }
        .ev-status {
          font-size: 0.7rem;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 2px 8px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .ev-status.idle {
          color: #71717a;
          background: rgba(113, 113, 122, 0.1);
        }
        .ev-status.charging {
          color: #22c55e;
          background: rgba(34, 197, 94, 0.15);
        }
        .ev-status.affected {
          color: #ef4444;
          background: rgba(239, 68, 68, 0.2);
          animation: status-blink 0.6s ease-in-out infinite;
        }
        .impact-details {
          margin-top: 6px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          max-width: 120px;
        }
        .impact-cve {
          font-size: 0.55rem;
          font-family: 'JetBrains Mono', monospace;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.15);
          padding: 1px 4px;
          border-radius: 2px;
        }
        .impact-text {
          font-size: 0.6rem;
          color: #fca5a5;
          text-align: center;
          line-height: 1.3;
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
        }
        @keyframes attack-glow {
          0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.15); }
        }
        @keyframes pulse-subtle {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes pulse-fast {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.1); }
        }
        @keyframes affected-pulse {
          0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(239, 68, 68, 0.3); }
          50% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 35px rgba(239, 68, 68, 0.5); }
        }
        @keyframes icon-shake {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-3deg); }
          75% { transform: rotate(3deg); }
        }
        @keyframes indicator-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }
        @keyframes status-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </div>
  )
}

function EVSENode({ data, selected }) {
  const state = data.state || 'Available'
  const isCharging = state === 'Charging'
  const power = data.power || 0
  const impact = useStore((state) => state.infrastructureImpact.evse)
  const isAffected = !!impact
  
  const stateConfig = {
    Charging: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)', icon: Zap },
    Available: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', icon: PlugZap },
    Preparing: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', icon: Activity },
    Faulted: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', icon: AlertTriangle },
    Unavailable: { color: '#71717a', bg: 'rgba(113, 113, 122, 0.1)', icon: PlugZap },
  }
  const config = isAffected 
    ? { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)', icon: ShieldAlert }
    : (stateConfig[state] || stateConfig.Unavailable)
  const StateIcon = config.icon

  return (
    <div 
      className={`evse-node-3d ${selected ? 'selected' : ''} ${isAffected ? 'affected' : ''}`} 
      style={{ '--state-color': config.color, '--state-bg': config.bg }}
    >
      <Handle type="target" position={Position.Left} id="in" className="handle-amber" />
      <Handle type="source" position={Position.Right} id="out" className="handle-amber" />
      
      {/* Electric glow effect */}
      {isCharging && !isAffected && <div className="evse-glow" />}
      {isAffected && <div className="evse-attack-glow" />}
      
      <div className="evse-header">
        <div className={`evse-icon-wrap ${isAffected ? 'affected' : ''}`} style={{ borderColor: config.color }}>
          {isAffected ? <ShieldAlert size={28} style={{ color: '#ef4444' }} /> : <PlugZap size={28} style={{ color: config.color }} />}
        </div>
        {isCharging && !isAffected && (
          <div className="power-badge">
            <Zap size={10} />
            {power > 0 ? `${(power/1000).toFixed(1)}kW` : 'ON'}
          </div>
        )}
        {isAffected && (
          <div className="attack-badge">
            <AlertTriangle size={10} />
            BREACH
          </div>
        )}
      </div>
      
      <div className="evse-info">
        <span className="evse-label">{data.label}</span>
        {isAffected ? (
          <>
            <div className="evse-state affected" style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.2)' }}>
              <ShieldAlert size={12} />
              COMPROMISED
            </div>
            <div className="evse-impact">
              <span className="impact-cve">{impact.cve}</span>
              <span className="impact-text">{impact.impact}</span>
            </div>
          </>
        ) : (
          <div className="evse-state" style={{ color: config.color, background: config.bg }}>
            <StateIcon size={12} />
            {state}
          </div>
        )}
      </div>
      
      {/* Connector visualization */}
      <div className="evse-connector">
        <div className={`connector-port ${isCharging ? 'active' : ''} ${isAffected ? 'compromised' : ''}`}>
          <div className="port-inner" />
        </div>
        {isCharging && !isAffected && <div className="cable-active" />}
        {isAffected && <div className="cable-compromised" />}
      </div>
      
      <style>{`
        .evse-node-3d {
          padding: 16px;
          background: linear-gradient(145deg, #1c1e22 0%, #141518 100%);
          border: 2px solid #3a3d44;
          border-radius: 16px;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.03) inset;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          min-width: 110px;
        }
        .evse-node-3d:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            0 0 20px rgba(245, 158, 11, 0.15);
          border-color: #4a4e58;
        }
        .evse-node-3d.selected {
          border-color: #f59e0b;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 30px rgba(245, 158, 11, 0.25);
        }
        .evse-node-3d.affected {
          border-color: #ef4444;
          animation: evse-affected-pulse 1s ease-in-out infinite;
        }
        .evse-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 14px;
          background: radial-gradient(ellipse at center, rgba(34, 197, 94, 0.1) 0%, transparent 70%);
          pointer-events: none;
        }
        .evse-attack-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 14px;
          background: radial-gradient(ellipse at center, rgba(239, 68, 68, 0.2) 0%, transparent 70%);
          pointer-events: none;
          animation: attack-glow-pulse 0.8s ease-in-out infinite;
        }
        .evse-header {
          display: flex;
          justify-content: center;
          align-items: center;
          position: relative;
          margin-bottom: 10px;
        }
        .evse-icon-wrap {
          width: 52px;
          height: 52px;
          border-radius: 12px;
          border: 2px solid;
          background: rgba(0, 0, 0, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s;
        }
        .evse-icon-wrap.affected {
          animation: icon-shake 0.3s ease-in-out infinite;
          background: rgba(239, 68, 68, 0.1);
        }
        .power-badge {
          position: absolute;
          top: -6px;
          right: 0;
          background: #22c55e;
          color: white;
          font-size: 0.6rem;
          font-weight: 700;
          padding: 2px 6px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 2px;
          box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
        }
        .attack-badge {
          position: absolute;
          top: -6px;
          right: -8px;
          background: linear-gradient(90deg, #dc2626, #ef4444);
          color: white;
          font-size: 0.55rem;
          font-weight: 700;
          padding: 3px 6px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 2px;
          box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
          animation: badge-pulse 0.6s ease-in-out infinite;
        }
        .evse-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
        }
        .evse-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: #f4f4f5;
        }
        .evse-state {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.65rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 3px 8px;
          border-radius: 4px;
        }
        .evse-state.affected {
          animation: status-blink 0.5s ease-in-out infinite;
        }
        .evse-impact {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          max-width: 130px;
        }
        .evse-impact .impact-cve {
          font-size: 0.55rem;
          font-family: 'JetBrains Mono', monospace;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.15);
          padding: 1px 4px;
          border-radius: 2px;
        }
        .evse-impact .impact-text {
          font-size: 0.6rem;
          color: #fca5a5;
          text-align: center;
          line-height: 1.3;
        }
        .evse-connector {
          margin-top: 10px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .connector-port {
          width: 24px;
          height: 16px;
          background: #0c0d0f;
          border-radius: 4px;
          border: 2px solid #3a3d44;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s;
        }
        .connector-port.active {
          border-color: #22c55e;
          box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
        }
        .connector-port.compromised {
          border-color: #ef4444;
          box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
          animation: port-alert 0.5s ease-in-out infinite;
        }
        .port-inner {
          width: 8px;
          height: 6px;
          background: #3a3d44;
          border-radius: 2px;
        }
        .connector-port.active .port-inner {
          background: #22c55e;
        }
        .connector-port.compromised .port-inner {
          background: #ef4444;
        }
        .cable-active {
          width: 4px;
          height: 12px;
          background: linear-gradient(180deg, #22c55e 0%, transparent 100%);
          border-radius: 2px;
          animation: cable-pulse 1s ease-in-out infinite;
        }
        .cable-compromised {
          width: 4px;
          height: 12px;
          background: linear-gradient(180deg, #ef4444 0%, transparent 100%);
          border-radius: 2px;
          animation: cable-alert 0.4s ease-in-out infinite;
        }
        @keyframes cable-pulse {
          0%, 100% { opacity: 1; height: 12px; }
          50% { opacity: 0.6; height: 8px; }
        }
        @keyframes cable-alert {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes evse-affected-pulse {
          0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(239, 68, 68, 0.3); }
          50% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 40px rgba(239, 68, 68, 0.5); }
        }
        @keyframes attack-glow-pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        @keyframes icon-shake {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-5deg); }
          75% { transform: rotate(5deg); }
        }
        @keyframes badge-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        @keyframes status-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        @keyframes port-alert {
          0%, 100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
          50% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.8); }
        }
      `}</style>
    </div>
  )
}

function CSMSNode({ data, selected }) {
  const isOnline = data.status === 'online'
  const connections = data.connections || 0
  const impact = useStore((state) => state.infrastructureImpact.csms)
  const isAffected = !!impact
  
  return (
    <div className={`csms-node-3d ${isOnline ? 'online' : 'offline'} ${selected ? 'selected' : ''} ${isAffected ? 'affected' : ''}`}>
      <Handle type="target" position={Position.Left} id="in" className="handle-amber" />
      
      {/* Server glow */}
      {isOnline && !isAffected && <div className="csms-glow" />}
      {isAffected && <div className="csms-attack-glow" />}
      
      <div className="csms-icon-container">
        <div className={`server-rack ${isAffected ? 'affected' : ''}`}>
          <Server size={40} className={`server-icon ${isAffected ? 'affected' : ''}`} />
          <div className="server-leds">
            {[0, 1, 2, 3].map(i => (
              <div 
                key={i} 
                className={`led ${isOnline ? 'active' : ''} ${i < connections ? 'connected' : ''} ${isAffected ? 'alert' : ''}`}
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
          {isAffected && (
            <div className="server-alert-badge">
              <AlertTriangle size={14} />
            </div>
          )}
        </div>
      </div>
      
      <div className="csms-info">
        <span className="csms-label">{data.label}</span>
        {isAffected ? (
          <>
            <div className="csms-status affected">
              <ShieldAlert size={12} />
              BREACH DETECTED
            </div>
            <div className="csms-impact">
              <span className="impact-cve">{impact.cve}</span>
              <span className="impact-text">{impact.impact}</span>
            </div>
          </>
        ) : (
          <>
            <div className={`csms-status ${isOnline ? 'online' : 'offline'}`}>
              {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
              {isOnline ? 'Online' : 'Offline'}
            </div>
            {connections > 0 && (
              <div className="csms-connections">
                <PlugZap size={10} />
                {connections} connected
              </div>
            )}
          </>
        )}
      </div>
      
      <style>{`
        .csms-node-3d {
          padding: 16px 20px;
          background: linear-gradient(145deg, #1c1e22 0%, #141518 100%);
          border: 2px solid #3a3d44;
          border-radius: 16px;
          box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.5),
            0 0 0 1px rgba(255, 255, 255, 0.03) inset;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          min-width: 130px;
        }
        .csms-node-3d:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 14px 50px rgba(0, 0, 0, 0.6),
            0 0 25px rgba(245, 158, 11, 0.15);
          border-color: #4a4e58;
        }
        .csms-node-3d.online {
          border-color: rgba(245, 158, 11, 0.4);
        }
        .csms-node-3d.offline {
          border-color: rgba(239, 68, 68, 0.4);
        }
        .csms-node-3d.affected {
          border-color: #ef4444;
          animation: csms-affected-pulse 1s ease-in-out infinite;
        }
        .csms-node-3d.selected {
          border-color: #f59e0b;
          box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.5),
            0 0 35px rgba(245, 158, 11, 0.3);
        }
        .csms-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 14px;
          background: radial-gradient(ellipse at top, rgba(245, 158, 11, 0.08) 0%, transparent 60%);
          pointer-events: none;
        }
        .csms-attack-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 14px;
          background: radial-gradient(ellipse at top, rgba(239, 68, 68, 0.2) 0%, transparent 60%);
          pointer-events: none;
          animation: csms-glow-pulse 0.8s ease-in-out infinite;
        }
        .csms-icon-container {
          display: flex;
          justify-content: center;
          margin-bottom: 12px;
        }
        .server-rack {
          position: relative;
          padding: 12px;
          background: linear-gradient(180deg, #252830 0%, #1c1e22 100%);
          border-radius: 10px;
          border: 1px solid #3a3d44;
          transition: all 0.3s;
        }
        .server-rack.affected {
          border-color: #ef4444;
          background: linear-gradient(180deg, #2d1f1f 0%, #1c1518 100%);
          animation: rack-shake 0.3s ease-in-out infinite;
        }
        .server-icon {
          color: #f59e0b;
          filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.3));
          transition: all 0.3s;
        }
        .server-icon.affected {
          color: #ef4444;
          filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
        }
        .online .server-icon:not(.affected) {
          animation: server-pulse 3s ease-in-out infinite;
        }
        .server-leds {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          flex-direction: column;
          gap: 3px;
        }
        .led {
          width: 4px;
          height: 4px;
          border-radius: 50%;
          background: #3a3d44;
          transition: all 0.3s;
        }
        .led.active {
          background: #f59e0b;
          box-shadow: 0 0 4px rgba(245, 158, 11, 0.6);
          animation: led-blink 2s ease-in-out infinite;
        }
        .led.connected {
          background: #22c55e;
          box-shadow: 0 0 4px rgba(34, 197, 94, 0.6);
        }
        .led.alert {
          background: #ef4444 !important;
          box-shadow: 0 0 6px rgba(239, 68, 68, 0.8) !important;
          animation: led-alert 0.3s ease-in-out infinite !important;
        }
        .server-alert-badge {
          position: absolute;
          top: -8px;
          right: -8px;
          background: #ef4444;
          border-radius: 50%;
          padding: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          animation: alert-badge-pulse 0.5s ease-in-out infinite;
          box-shadow: 0 2px 8px rgba(239, 68, 68, 0.6);
        }
        .csms-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .csms-label {
          font-size: 0.9rem;
          font-weight: 600;
          color: #f4f4f5;
        }
        .csms-status {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.65rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          padding: 3px 8px;
          border-radius: 4px;
        }
        .csms-status.online {
          color: #f59e0b;
          background: rgba(245, 158, 11, 0.15);
        }
        .csms-status.offline {
          color: #ef4444;
          background: rgba(239, 68, 68, 0.15);
        }
        .csms-status.affected {
          color: #ef4444;
          background: rgba(239, 68, 68, 0.2);
          animation: status-blink 0.5s ease-in-out infinite;
        }
        .csms-connections {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.7rem;
          color: #a1a1aa;
        }
        .csms-impact {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          max-width: 140px;
          margin-top: 4px;
        }
        .csms-impact .impact-cve {
          font-size: 0.55rem;
          font-family: 'JetBrains Mono', monospace;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.15);
          padding: 1px 4px;
          border-radius: 2px;
        }
        .csms-impact .impact-text {
          font-size: 0.6rem;
          color: #fca5a5;
          text-align: center;
          line-height: 1.3;
        }
        @keyframes server-pulse {
          0%, 100% { filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.3)); }
          50% { filter: drop-shadow(0 0 12px rgba(245, 158, 11, 0.5)); }
        }
        @keyframes led-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes led-alert {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.3); }
        }
        @keyframes csms-affected-pulse {
          0%, 100% { box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 25px rgba(239, 68, 68, 0.3); }
          50% { box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 45px rgba(239, 68, 68, 0.5); }
        }
        @keyframes csms-glow-pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        @keyframes rack-shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-2px); }
          75% { transform: translateX(2px); }
        }
        @keyframes alert-badge-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }
        @keyframes status-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Vulnerable EVSE Node - Threat indicators with amber theme
// ═══════════════════════════════════════════════════════════

function VulnerableEVSENode({ data, selected }) {
  const state = data.state || 'Available'
  const isCompromised = data.compromised || false
  const cves = data.cves || []
  const port = data.port || 8080
  
  // Check if this target is under attack - use selector for reactive updates
  const targetKey = `evcr-vulnerable-cps:${port}`
  const attackInfo = useStore((state) => state.activeAttacks[targetKey])
  const isUnderAttack = !!attackInfo && !attackInfo.completed
  const wasCompromised = attackInfo?.completed && attackInfo?.success

  return (
    <div className={`vuln-node-3d ${selected ? 'selected' : ''} ${isCompromised || wasCompromised ? 'compromised' : ''} ${isUnderAttack ? 'under-attack' : ''}`}>
      <Handle type="target" position={Position.Left} id="in" className="handle-danger" />
      <Handle type="source" position={Position.Right} id="out" className="handle-danger" />
      
      {/* Danger glow */}
      <div className={`vuln-glow ${isCompromised || wasCompromised ? 'compromised' : ''} ${isUnderAttack ? 'under-attack' : ''}`} />
      
      {/* Attack indicator overlay */}
      {isUnderAttack && (
        <div className="attack-overlay">
          <div className="attack-scanner" />
          <div className="attack-pulse" />
        </div>
      )}
      
      <div className="vuln-header">
        <div className={`vuln-icon-wrap ${isCompromised || wasCompromised ? 'compromised' : ''} ${isUnderAttack ? 'under-attack' : ''}`}>
          <ShieldAlert size={28} />
        </div>
        <div className="vuln-vendor">{data.vendor || 'Unknown'}</div>
      </div>
      
      <div className="vuln-body">
        <span className="vuln-label">{data.label}</span>
        <span className="vuln-model">{data.model || 'EVSE'}</span>
        
        <div className="vuln-cves">
          {cves.slice(0, 2).map((cve, i) => (
            <span key={i} className={`cve-badge ${attackInfo?.cve === cve ? 'active' : ''}`}>{cve}</span>
          ))}
        </div>
        
        <a 
          href={`http://localhost:${port}`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="vuln-port"
          onClick={(e) => e.stopPropagation()}
        >
          <Activity size={10} />
          :{port}
        </a>
      </div>
      
      {isUnderAttack && (
        <div className="attack-banner">
          <AlertTriangle size={10} className="attack-icon-pulse" />
          UNDER ATTACK
          <span className="attack-cve">{attackInfo?.cve}</span>
        </div>
      )}
      
      {(isCompromised || wasCompromised) && !isUnderAttack && (
        <div className="compromised-banner">
          <AlertTriangle size={10} />
          COMPROMISED
        </div>
      )}
      
      <style>{`
        .vuln-node-3d {
          background: linear-gradient(145deg, #1c1e22 0%, #141518 100%);
          border: 2px solid rgba(239, 68, 68, 0.4);
          border-radius: 16px;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 20px rgba(239, 68, 68, 0.1);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          width: 150px;
          overflow: hidden;
        }
        .vuln-node-3d:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            0 0 30px rgba(239, 68, 68, 0.2);
        }
        .vuln-node-3d.compromised {
          border-color: #ef4444;
          animation: danger-pulse 2s ease-in-out infinite;
        }
        .vuln-node-3d.under-attack {
          border-color: #f97316;
          animation: attack-border 0.5s ease-in-out infinite;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            0 0 40px rgba(249, 115, 22, 0.4),
            0 0 60px rgba(249, 115, 22, 0.2);
        }
        .vuln-node-3d.selected {
          border-color: #f59e0b;
        }
        .vuln-glow {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 60px;
          background: radial-gradient(ellipse at top, rgba(239, 68, 68, 0.1) 0%, transparent 70%);
          pointer-events: none;
        }
        .vuln-glow.compromised {
          background: radial-gradient(ellipse at top, rgba(239, 68, 68, 0.2) 0%, transparent 70%);
        }
        .vuln-glow.under-attack {
          background: radial-gradient(ellipse at top, rgba(249, 115, 22, 0.3) 0%, transparent 70%);
          animation: glow-pulse 0.8s ease-in-out infinite;
        }
        
        /* Attack overlay effects */
        .attack-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
          overflow: hidden;
          border-radius: 14px;
        }
        .attack-scanner {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, transparent, #f97316, transparent);
          animation: scan-down 1.5s ease-in-out infinite;
        }
        .attack-pulse {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 200%;
          height: 200%;
          transform: translate(-50%, -50%);
          background: radial-gradient(circle, rgba(249, 115, 22, 0.1) 0%, transparent 50%);
          animation: pulse-out 1s ease-out infinite;
        }
        
        .vuln-header {
          padding: 12px;
          display: flex;
          align-items: center;
          gap: 10px;
          border-bottom: 1px solid rgba(239, 68, 68, 0.2);
        }
        .vuln-icon-wrap {
          width: 42px;
          height: 42px;
          border-radius: 10px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ef4444;
        }
        .vuln-icon-wrap.compromised {
          background: rgba(239, 68, 68, 0.2);
          animation: icon-pulse 1.5s ease-in-out infinite;
        }
        .vuln-icon-wrap.under-attack {
          background: rgba(249, 115, 22, 0.3);
          border-color: #f97316;
          color: #f97316;
          animation: icon-shake 0.3s ease-in-out infinite;
        }
        .vuln-vendor {
          font-size: 0.6rem;
          font-weight: 700;
          color: #71717a;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .vuln-body {
          padding: 10px 12px 12px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .vuln-label {
          font-size: 0.8rem;
          font-weight: 600;
          color: #f4f4f5;
        }
        .vuln-model {
          font-size: 0.65rem;
          color: #71717a;
        }
        .vuln-cves {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin: 6px 0;
        }
        .cve-badge {
          font-size: 0.55rem;
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
          padding: 2px 6px;
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
          border-radius: 3px;
          border: 1px solid rgba(239, 68, 68, 0.2);
          transition: all 0.3s;
        }
        .cve-badge.active {
          background: rgba(249, 115, 22, 0.3);
          color: #f97316;
          border-color: #f97316;
          animation: cve-blink 0.5s ease-in-out infinite;
        }
        .vuln-port {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          width: fit-content;
          font-size: 0.7rem;
          font-family: 'JetBrains Mono', monospace;
          color: #f59e0b;
          text-decoration: none;
          padding: 4px 8px;
          background: rgba(245, 158, 11, 0.1);
          border-radius: 4px;
          transition: all 0.2s;
        }
        .vuln-port:hover {
          background: rgba(245, 158, 11, 0.2);
        }
        .attack-banner {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 8px;
          background: linear-gradient(90deg, #ea580c, #f97316, #ea580c);
          background-size: 200% 100%;
          animation: gradient-shift 1s linear infinite;
          color: white;
          font-size: 0.6rem;
          font-weight: 700;
          letter-spacing: 0.1em;
        }
        .attack-cve {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.55rem;
          opacity: 0.9;
        }
        .attack-icon-pulse {
          animation: icon-pulse-fast 0.4s ease-in-out infinite;
        }
        .compromised-banner {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 6px;
          background: linear-gradient(90deg, #dc2626, #b91c1c);
          color: white;
          font-size: 0.6rem;
          font-weight: 700;
          letter-spacing: 0.1em;
        }
        .handle-danger {
          background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        }
        @keyframes danger-pulse {
          0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(239, 68, 68, 0.2); }
          50% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 35px rgba(239, 68, 68, 0.4); }
        }
        @keyframes attack-border {
          0%, 100% { border-color: #f97316; }
          50% { border-color: #fbbf24; }
        }
        @keyframes glow-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes scan-down {
          0% { top: 0; opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        @keyframes pulse-out {
          0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.5; }
          100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
        }
        @keyframes icon-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes icon-shake {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-5deg); }
          75% { transform: rotate(5deg); }
        }
        @keyframes icon-pulse-fast {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
        }
        @keyframes cve-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        @keyframes gradient-shift {
          0% { background-position: 0% 50%; }
          100% { background-position: 200% 50%; }
        }
      `}</style>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Kali Attacker Node - Red Team terminal with official logo
// ═══════════════════════════════════════════════════════════

function KaliNode({ data, selected }) {
  // Get active attacks to show attack status
  const activeAttacks = useStore((state) => state.activeAttacks)
  const attackCount = Object.keys(activeAttacks).filter(k => !activeAttacks[k]?.completed).length
  const isAttacking = attackCount > 0
  const currentTarget = Object.keys(activeAttacks).find(k => !activeAttacks[k]?.completed)
  const currentCVE = currentTarget ? activeAttacks[currentTarget]?.cve : null

  return (
    <div className={`kali-node-3d ${selected ? 'selected' : ''} ${isAttacking ? 'attacking' : ''}`}>
      <Handle type="source" position={Position.Right} id="attack-out" className="handle-attack" />
      
      {/* Attack pulse effect */}
      {isAttacking && <div className="kali-attack-pulse" />}
      
      <div className="kali-header">
        <div className={`kali-icon-wrap ${isAttacking ? 'attacking' : ''}`}>
          {isAttacking ? (
            <Crosshair size={32} className="crosshair-spin" />
          ) : (
            <img 
              src="/images/kali-dragon.svg" 
              alt="Kali Linux" 
              className="kali-dragon-logo"
            />
          )}
        </div>
        <div className="kali-badge">KALI LINUX</div>
      </div>
      
      <div className="kali-info">
        <span className="kali-label">{data.label}</span>
        <div className={`kali-status ${isAttacking ? 'attacking' : 'idle'}`}>
          {isAttacking ? (
            <>
              <Activity size={10} className="activity-pulse" />
              ATTACKING
            </>
          ) : (
            <>
              <span className="status-dot"></span>
              READY
            </>
          )}
        </div>
        {isAttacking && currentCVE && (
          <div className="kali-target">
            <span className="target-cve">{currentCVE}</span>
          </div>
        )}
      </div>
      
      <style>{`
        .kali-node-3d {
          padding: 14px 16px;
          background: linear-gradient(145deg, #0d1117 0%, #161b22 100%);
          border: 2px solid #2778c4;
          border-radius: 16px;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.5),
            0 0 20px rgba(39, 120, 196, 0.25);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          min-width: 120px;
        }
        .kali-node-3d:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.6),
            0 0 30px rgba(139, 0, 139, 0.25);
        }
        .kali-node-3d.attacking {
          border-color: #dc2626;
          animation: kali-pulse 1.5s ease-in-out infinite;
          box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(220, 38, 38, 0.4);
        }
        .kali-node-3d.selected {
          border-color: #8b5cf6;
        }
        .kali-attack-pulse {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 150%;
          height: 150%;
          transform: translate(-50%, -50%);
          background: radial-gradient(circle, rgba(220, 38, 38, 0.2) 0%, transparent 60%);
          border-radius: 50%;
          animation: attack-radiate 1s ease-out infinite;
          pointer-events: none;
        }
        .kali-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }
        .kali-icon-wrap {
          width: 52px;
          height: 52px;
          border-radius: 12px;
          background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
          border: 1px solid rgba(39, 120, 196, 0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #58a6ff;
          transition: all 0.3s;
          overflow: hidden;
        }
        .kali-dragon-logo {
          width: 44px;
          height: 44px;
          object-fit: contain;
          filter: drop-shadow(0 0 4px rgba(39, 120, 196, 0.5));
        }
        .kali-icon-wrap.attacking {
          background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
          border-color: #dc2626;
          color: #fca5a5;
          animation: icon-glow 0.5s ease-in-out infinite;
        }
        .crosshair-spin {
          animation: spin-slow 2s linear infinite;
        }
        .kali-badge {
          font-size: 0.55rem;
          font-weight: 800;
          color: #58a6ff;
          background: rgba(39, 120, 196, 0.15);
          padding: 3px 8px;
          border-radius: 4px;
          letter-spacing: 0.15em;
        }
        .kali-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .kali-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: #e2e8f0;
        }
        .kali-status {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.6rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          padding: 3px 8px;
          border-radius: 4px;
          width: fit-content;
        }
        .kali-status.idle {
          color: #58a6ff;
          background: rgba(39, 120, 196, 0.15);
        }
        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #58a6ff;
          margin-right: 4px;
        }
        .kali-status.attacking {
          color: #fca5a5;
          background: rgba(220, 38, 38, 0.2);
          animation: status-blink 0.8s ease-in-out infinite;
        }
        .activity-pulse {
          animation: pulse-fast 0.6s ease-in-out infinite;
        }
        .kali-target {
          margin-top: 4px;
        }
        .target-cve {
          font-size: 0.55rem;
          font-family: 'JetBrains Mono', monospace;
          color: #f87171;
          background: rgba(220, 38, 38, 0.15);
          padding: 2px 6px;
          border-radius: 3px;
        }
        .handle-attack {
          width: 14px !important;
          height: 14px !important;
          background: linear-gradient(135deg, #dc2626, #991b1b) !important;
          border: 2px solid rgba(255, 255, 255, 0.2) !important;
          box-shadow: 0 0 10px rgba(220, 38, 38, 0.5) !important;
        }
        @keyframes kali-pulse {
          0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 30px rgba(220, 38, 38, 0.3); }
          50% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 50px rgba(220, 38, 38, 0.5); }
        }
        @keyframes attack-radiate {
          0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
          100% { transform: translate(-50%, -50%) scale(1.2); opacity: 0; }
        }
        @keyframes icon-glow {
          0%, 100% { filter: drop-shadow(0 0 4px rgba(220, 38, 38, 0.5)); }
          50% { filter: drop-shadow(0 0 12px rgba(220, 38, 38, 0.8)); }
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes status-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        @keyframes pulse-fast {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.3); }
        }
      `}</style>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Electric Grid Background
// ═══════════════════════════════════════════════════════════

function ElectricGridBackground() {
  return (
    <div className="electric-grid-bg">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          {/* Main grid */}
          <pattern id="smallGrid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path 
              d="M 40 0 L 0 0 0 40" 
              fill="none" 
              stroke="rgba(245, 158, 11, 0.04)" 
              strokeWidth="0.5"
            />
          </pattern>
          <pattern id="largeGrid" width="200" height="200" patternUnits="userSpaceOnUse">
            <rect width="200" height="200" fill="url(#smallGrid)"/>
            <path 
              d="M 200 0 L 0 0 0 200" 
              fill="none" 
              stroke="rgba(245, 158, 11, 0.08)" 
              strokeWidth="1"
            />
          </pattern>
          
          {/* Radial fade */}
          <radialGradient id="gridFade" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="100%" stopColor="rgba(12, 13, 15, 0.9)" />
          </radialGradient>
        </defs>
        
        <rect width="100%" height="100%" fill="url(#largeGrid)" />
        <rect width="100%" height="100%" fill="url(#gridFade)" />
      </svg>
      
      <style>{`
        .electric-grid-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
          background: linear-gradient(180deg, #0c0d0f 0%, #141518 50%, #0c0d0f 100%);
        }
      `}</style>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Global Handle Styles
// ═══════════════════════════════════════════════════════════

const globalStyles = `
  .handle-amber {
    width: 14px !important;
    height: 14px !important;
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 
      0 2px 6px rgba(0, 0, 0, 0.4),
      0 0 10px rgba(245, 158, 11, 0.3) !important;
    transition: all 0.2s ease !important;
  }
  .handle-amber:hover {
    transform: scale(1.2) !important;
    box-shadow: 
      0 3px 10px rgba(0, 0, 0, 0.5),
      0 0 15px rgba(245, 158, 11, 0.5) !important;
  }
`

// ═══════════════════════════════════════════════════════════
// Main Canvas Component
// ═══════════════════════════════════════════════════════════

const nodeTypes = {
  ev: EVNode,
  evse: EVSENode,
  csms: CSMSNode,
  vulnerable_evse: VulnerableEVSENode,
  kali: KaliNode,
}

const initialNodes = [
  // ═══════════════════════════════════════════════════════════
  // ZONA LEGITIMA (Izquierda) - Infraestructura de carga
  // ═══════════════════════════════════════════════════════════
  
  // Electric Vehicle
  {
    id: 'ev-1',
    type: 'ev',
    position: { x: 50, y: 200 },
    data: { label: 'EV-Tesla', state: 'Idle' },
  },
  
  // Legitimate EVSE
  {
    id: 'evse-1',
    type: 'evse',
    position: { x: 230, y: 200 },
    data: { label: 'EVSE-001', state: 'Available', power: 0 },
  },
  
  // CSMS Server (centro)
  {
    id: 'csms-1',
    type: 'csms',
    position: { x: 420, y: 200 },
    data: { label: 'CSMS Server', status: 'online', connections: 1 },
  },

  // ═══════════════════════════════════════════════════════════
  // ZONA VULNERABLE (Derecha) - Targets de los CVEs
  // ═══════════════════════════════════════════════════════════
  
  // Fila superior de vulnerables
  {
    id: 'vuln-hardy',
    type: 'vulnerable_evse',
    position: { x: 680, y: 20 },
    data: { 
      label: 'Hardy Barth', 
      vendor: 'Hardy Barth',
      model: 'eCB1 Wallbox',
      port: 8081,
      cves: ['CVE-2024-11665', 'CVE-2024-11666']
    },
  },
  {
    id: 'vuln-schneider',
    type: 'vulnerable_evse',
    position: { x: 880, y: 20 },
    data: { 
      label: 'Schneider EVlink', 
      vendor: 'Schneider',
      model: 'EVlink City',
      port: 8082,
      cves: ['CVE-2018-7800']
    },
  },
  {
    id: 'vuln-wallbox',
    type: 'vulnerable_evse',
    position: { x: 1080, y: 20 },
    data: { 
      label: 'Wallbox Pulsar', 
      vendor: 'Wallbox',
      model: 'Pulsar Plus',
      port: 8083,
      cves: ['CVE-2023-32249']
    },
  },
  
  // Fila inferior de vulnerables
  {
    id: 'vuln-chargepoint',
    type: 'vulnerable_evse',
    position: { x: 680, y: 220 },
    data: { 
      label: 'ChargePoint', 
      vendor: 'ChargePoint',
      model: 'Home Flex',
      port: 8084,
      cves: ['CVE-2022-26132']
    },
  },
  {
    id: 'vuln-abbcred',
    type: 'vulnerable_evse',
    position: { x: 880, y: 220 },
    data: { 
      label: 'ABB Terra', 
      vendor: 'ABB',
      model: 'Terra AC',
      port: 8085,
      cves: ['CVE-2024-43659']
    },
  },
  {
    id: 'vuln-iso15118',
    type: 'vulnerable_evse',
    position: { x: 1080, y: 220 },
    data: { 
      label: 'ISO15118 Target', 
      vendor: 'Generic',
      model: 'ISO15118 Stack',
      port: 8086,
      cves: ['CVE-2025-12357']
    },
  },

  // ═══════════════════════════════════════════════════════════
  // ATACANTE (Centro-abajo) - Kali Linux
  // ═══════════════════════════════════════════════════════════
  {
    id: 'kali-1',
    type: 'kali',
    position: { x: 880, y: 420 },
    data: { label: 'Kali Linux' },
  },
]

const initialEdges = [
  // Legitimate infrastructure connections
  { 
    id: 'e1', 
    source: 'ev-1', 
    target: 'evse-1', 
    animated: false, 
    style: { stroke: '#3a3d44', strokeWidth: 3 },
    type: 'smoothstep',
  },
  { 
    id: 'e2', 
    source: 'evse-1', 
    target: 'csms-1', 
    animated: true, 
    style: { stroke: '#f59e0b', strokeWidth: 2 },
    type: 'smoothstep',
  },
  
  // Kali connected to all vulnerable targets (potential attack paths)
  { 
    id: 'kali-hardy', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-hardy',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
  { 
    id: 'kali-schneider', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-schneider',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
  { 
    id: 'kali-wallbox', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-wallbox',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
  { 
    id: 'kali-chargepoint', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-chargepoint',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
  { 
    id: 'kali-abb', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-abbcred',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
  { 
    id: 'kali-iso', 
    source: 'kali-1',
    sourceHandle: 'attack-out',
    target: 'vuln-iso15118',
    targetHandle: 'in',
    style: { stroke: '#374151', strokeWidth: 1, strokeDasharray: '5 5' },
    type: 'smoothstep',
  },
]

export default function TopologyCanvas({ onNodeSelect }) {
  const { chargePoints, connectivity, topologyNodes, topologyEdges, setTopologyNodes, setTopologyEdges, resetTopology, activeAttacks } = useStore()
  
  // Check if we need to reset to new layout (detect old layout)
  const needsReset = (topologyNodes && topologyNodes.length !== initialNodes.length) ||
    (topologyEdges && !topologyEdges.some(e => e.id === 'kali-hardy'))
  
  // Use persisted nodes/edges from store, or fallback to initial
  const [nodes, setNodes, onNodesChange] = useNodesState(
    needsReset ? initialNodes : (topologyNodes || initialNodes)
  )
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    needsReset ? initialEdges : (topologyEdges || initialEdges)
  )
  
  // Reset stored topology if layout changed
  useEffect(() => {
    if (needsReset) {
      resetTopology()
    }
  }, [needsReset, resetTopology])
  
  // Persist node positions when they change (but not edges - those are dynamic)
  useEffect(() => {
    if (nodes && nodes.length > 0 && !needsReset) {
      setTopologyNodes(nodes)
    }
  }, [nodes, setTopologyNodes, needsReset])

  // Map port to node ID for attack edges
  const portToNodeId = {
    8081: 'vuln-hardy',
    8082: 'vuln-schneider', 
    8083: 'vuln-wallbox',
    8084: 'vuln-chargepoint',
    8085: 'vuln-abbcred',
    8086: 'vuln-iso15118',
  }

  // Update nodes with real data
  const updatedNodes = useMemo(() => {
    return nodes.map(node => {
      if (node.type === 'evse') {
        const cp = chargePoints?.find(c => c.id === node.data.label)
        if (cp) {
          return {
            ...node,
            data: { ...node.data, state: cp.status || 'Available', power: 0 }
          }
        }
      }
      if (node.type === 'ev') {
        const evseId = node.id === 'ev-1' ? 'EVSE-001' : 'EVSE-002'
        const cp = chargePoints?.find(c => c.id === evseId)
        return {
          ...node,
          data: { ...node.data, state: cp?.status === 'Charging' ? 'Charging' : 'Idle' }
        }
      }
      if (node.type === 'csms') {
        const isOnline = connectivity?.csms === true
        return {
          ...node,
          data: { ...node.data, status: isOnline ? 'online' : 'offline', connections: chargePoints?.length || 0 }
        }
      }
      return node
    })
  }, [nodes, chargePoints, connectivity])

  // Update edges based on charging state AND active attacks
  const updatedEdges = useMemo(() => {
    // Map of port to edge id for attack highlighting
    const portToEdgeId = {
      8081: 'kali-hardy',
      8082: 'kali-schneider',
      8083: 'kali-wallbox',
      8084: 'kali-chargepoint',
      8085: 'kali-abb',
      8086: 'kali-iso',
    }
    
    // Get active attack ports
    const activeAttackPorts = new Set()
    Object.entries(activeAttacks).forEach(([target, info]) => {
      if (!info?.completed) {
        const port = parseInt(target.split(':')[1])
        if (port) {
          activeAttackPorts.add(port)
        }
      }
    })
    
    // Update edges
    return edges.map(edge => {
      // Handle EV charging edges
      if (edge.source === 'ev-1') {
        const cp = chargePoints?.find(c => c.id === 'EVSE-001')
        const isCharging = cp?.status === 'Charging'
        return {
          ...edge,
          animated: isCharging,
          style: {
            ...edge.style,
            stroke: isCharging ? '#22c55e' : '#3a3d44',
            filter: isCharging ? 'drop-shadow(0 0 6px rgba(34, 197, 94, 0.6))' : 'none',
          }
        }
      }
      
      // Handle Kali attack edges - highlight when attacking
      if (edge.id.startsWith('kali-')) {
        // Find which port this edge targets by edge id
        const portEntry = Object.entries(portToEdgeId).find(([port, edgeId]) => edgeId === edge.id)
        const targetPort = portEntry ? parseInt(portEntry[0]) : null
        const isAttacking = targetPort && activeAttackPorts.has(targetPort)
        
        if (isAttacking) {
          return {
            ...edge,
            animated: true,
            style: {
              stroke: '#dc2626',
              strokeWidth: 3,
              strokeDasharray: '8 4',
              filter: 'drop-shadow(0 0 8px rgba(220, 38, 38, 0.8))',
            }
          }
        }
        // Return edge with default dormant style
        return {
          ...edge,
          animated: false,
          style: {
            stroke: '#374151',
            strokeWidth: 1,
            strokeDasharray: '5 5',
            filter: 'none',
          }
        }
      }
      
      return edge
    })
  }, [edges, chargePoints, activeAttacks])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({
      ...params,
      type: 'smoothstep',
      style: { stroke: '#f59e0b', strokeWidth: 2 },
      animated: true,
    }, eds)),
    [setEdges],
  )

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('componentType')
      if (!type) return

      const position = { x: event.clientX - 200, y: event.clientY - 100 }
      let newNode

      if (type === 'vulnerable_evse') {
        const vulnCpData = event.dataTransfer.getData('vulnCpData')
        if (vulnCpData) {
          const vulnCp = JSON.parse(vulnCpData)
          newNode = {
            id: `vuln-${vulnCp.id}-${Date.now()}`,
            type: 'vulnerable_evse',
            position,
            data: {
              label: `CP-${vulnCp.id.toUpperCase().slice(0, 8)}`,
              vendor: vulnCp.vendor,
              model: vulnCp.model,
              state: 'Available',
              port: vulnCp.port,
              cves: vulnCp.cves,
              compromised: false,
            },
          }
        }
      } else {
        newNode = {
          id: `${type}-${Date.now()}`,
          type,
          position,
          data: {
            label: type === 'ev' ? 'New EV' : type === 'evse' ? 'New EVSE' : 'CSMS',
            state: type === 'ev' ? 'Idle' : 'Available',
          },
        }
      }

      if (newNode) setNodes((nds) => nds.concat(newNode))
    },
    [setNodes],
  )

  return (
    <div className="topology-container">
      <style>{globalStyles}</style>
      <ElectricGridBackground />
      <ReactFlow
        nodes={updatedNodes}
        edges={updatedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onNodeClick={(event, node) => {
          if (node.type === 'vulnerable_evse' && node.data.cves?.length > 0 && onNodeSelect) {
            onNodeSelect(node.data.cves[0])
          }
        }}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.4}
        maxZoom={2}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="transparent" />
        <Controls showInteractive={false} className="controls-amber" />
        <MiniMap 
          nodeColor={(node) => {
            if (node.type === 'csms') return '#f59e0b'
            if (node.type === 'evse') return '#22c55e'
            if (node.type === 'vulnerable_evse') return '#ef4444'
            return '#71717a'
          }}
          maskColor="rgba(12, 13, 15, 0.85)"
          className="minimap-amber"
        />
      </ReactFlow>
      
      <style>{`
        .topology-container {
          width: 100%;
          height: 100%;
          position: relative;
        }
        .controls-amber {
          background: linear-gradient(145deg, #1c1e22, #141518) !important;
          border: 1px solid rgba(245, 158, 11, 0.3) !important;
          border-radius: 12px !important;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
          overflow: hidden;
        }
        .controls-amber button {
          background: transparent !important;
          border-bottom: 1px solid rgba(245, 158, 11, 0.15) !important;
        }
        .controls-amber button:hover {
          background: rgba(245, 158, 11, 0.1) !important;
        }
        .controls-amber button svg {
          fill: #71717a !important;
        }
        .controls-amber button:hover svg {
          fill: #f59e0b !important;
        }
        .minimap-amber {
          background: linear-gradient(145deg, #1c1e22, #141518) !important;
          border: 1px solid rgba(245, 158, 11, 0.3) !important;
          border-radius: 12px !important;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        }
        .react-flow__edge.animated path {
          stroke-dasharray: 6;
          animation: flow-dash 0.6s linear infinite;
        }
        @keyframes flow-dash {
          to { stroke-dashoffset: -12; }
        }
      `}</style>
    </div>
  )
}
