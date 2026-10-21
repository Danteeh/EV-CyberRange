import { useCallback, useMemo, useState } from 'react'
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
import { Car, Zap, Server, Wifi, WifiOff } from 'lucide-react'

// ═══════════════════════════════════════════════════════════
// Custom Node Types - 2.5D Isometric Style
// ═══════════════════════════════════════════════════════════

function EVNode({ data, selected }) {
  const isCharging = data.state === 'Charging'
  
  return (
    <div className={`node-ev ${isCharging ? 'charging' : ''} ${selected ? 'selected' : ''}`}>
      <Handle type="source" position={Position.Right} id="out" />
      
      <div className="node-visual">
        <svg width="80" height="60" viewBox="0 0 80 60">
          {/* Shadow */}
          <ellipse cx="40" cy="55" rx="30" ry="6" fill="rgba(0,0,0,0.3)" />
          
          {/* Car body - isometric */}
          <path 
            d="M15 35 L40 25 L65 35 L65 45 L40 55 L15 45 Z" 
            fill={isCharging ? '#2c5282' : '#3d4451'}
            stroke="#4a5568"
            strokeWidth="1"
          />
          {/* Car roof */}
          <path 
            d="M22 30 L40 22 L58 30 L58 35 L40 43 L22 35 Z" 
            fill={isCharging ? '#3182ce' : '#4a5568'}
            stroke="#4a5568"
            strokeWidth="1"
          />
          {/* Wheels */}
          <ellipse cx="25" cy="48" rx="6" ry="3" fill="#1a202c" />
          <ellipse cx="55" cy="48" rx="6" ry="3" fill="#1a202c" />
          
          {/* Charging indicator */}
          {isCharging && (
            <g className="anim-pulse">
              <circle cx="40" cy="12" r="6" fill="#4a9f6e" opacity="0.3" />
              <circle cx="40" cy="12" r="4" fill="#4a9f6e" />
              <path d="M38 10 L42 10 L40 14 L43 14 L39 18 L40 14 L37 14 Z" fill="white" />
            </g>
          )}
        </svg>
      </div>
      
      <div className="node-label">{data.label}</div>
      {isCharging && <div className="node-status charging">Charging</div>}
      
      <style>{`
        .node-ev {
          padding: 8px;
          border-radius: 8px;
          background: var(--cr-surface);
          border: 2px solid var(--cr-border);
          transition: all 0.2s;
        }
        .node-ev.selected {
          border-color: var(--cr-accent);
          box-shadow: 0 0 0 2px rgba(77, 166, 168, 0.2);
        }
        .node-ev.charging {
          border-color: var(--cr-success);
        }
        .node-visual {
          display: flex;
          justify-content: center;
        }
        .node-label {
          text-align: center;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--cr-text);
          margin-top: 4px;
        }
        .node-status {
          text-align: center;
          font-size: 0.625rem;
          font-weight: 500;
          text-transform: uppercase;
          padding: 2px 6px;
          border-radius: 3px;
          margin-top: 4px;
        }
        .node-status.charging {
          background: rgba(74, 159, 110, 0.2);
          color: var(--cr-success);
        }
      `}</style>
    </div>
  )
}

function EVSENode({ data, selected }) {
  const state = data.state || 'Available'
  const isCharging = state === 'Charging'
  const power = data.power || 0
  
  const stateColor = {
    Charging: '#4a9f6e',
    Available: '#4da6a8',
    Preparing: '#c9913a',
    Faulted: '#c45c5c',
    Unavailable: '#5c6370',
  }[state] || '#5c6370'

  return (
    <div className={`node-evse ${selected ? 'selected' : ''}`} style={{ '--state-color': stateColor }}>
      <Handle type="target" position={Position.Left} id="in" />
      <Handle type="source" position={Position.Right} id="out" />
      
      <div className="node-visual">
        <svg width="60" height="80" viewBox="0 0 60 80">
          {/* Shadow */}
          <ellipse cx="30" cy="75" rx="20" ry="5" fill="rgba(0,0,0,0.3)" />
          
          {/* Base */}
          <path 
            d="M15 65 L30 72 L45 65 L45 70 L30 77 L15 70 Z" 
            fill="#2d3748"
            stroke="#4a5568"
            strokeWidth="1"
          />
          
          {/* Body - isometric column */}
          <path 
            d="M15 25 L30 18 L45 25 L45 65 L30 72 L15 65 Z" 
            fill={stateColor}
            stroke="#4a5568"
            strokeWidth="1"
            opacity="0.9"
          />
          
          {/* Screen */}
          <rect x="20" y="30" width="15" height="10" rx="1" 
                fill={isCharging ? '#4a9f6e' : '#1a202c'} />
          
          {/* Cable port */}
          <circle cx="30" cy="50" r="4" fill="#1a202c" stroke="#4a5568" />
          
          {/* Status LED */}
          <circle cx="30" cy="22" r="3" fill={stateColor} className={isCharging ? 'anim-pulse' : ''} />
        </svg>
      </div>
      
      <div className="node-label">{data.label}</div>
      <div className="node-state" style={{ color: stateColor }}>{state}</div>
      {isCharging && power > 0 && (
        <div className="node-power">{power.toFixed(0)} W</div>
      )}
      
      <style>{`
        .node-evse {
          padding: 8px;
          border-radius: 8px;
          background: var(--cr-surface);
          border: 2px solid var(--cr-border);
          transition: all 0.2s;
        }
        .node-evse.selected {
          border-color: var(--cr-accent);
          box-shadow: 0 0 0 2px rgba(77, 166, 168, 0.2);
        }
        .node-state {
          text-align: center;
          font-size: 0.625rem;
          font-weight: 500;
          text-transform: uppercase;
        }
        .node-power {
          text-align: center;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--cr-success);
        }
      `}</style>
    </div>
  )
}

function CSMSNode({ data, selected }) {
  const isOnline = data.status === 'online'
  
  return (
    <div className={`node-csms ${isOnline ? 'online' : 'offline'} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} id="in" />
      
      <div className="node-visual">
        <svg width="70" height="90" viewBox="0 0 70 90">
          {/* Shadow */}
          <ellipse cx="35" cy="85" rx="25" ry="5" fill="rgba(0,0,0,0.3)" />
          
          {/* Server rack - isometric */}
          <path 
            d="M10 20 L35 10 L60 20 L60 80 L35 90 L10 80 Z" 
            fill="#2d3748"
            stroke="#4a5568"
            strokeWidth="1"
          />
          
          {/* Server units */}
          {[0, 1, 2, 3].map(i => (
            <g key={i}>
              <rect x="15" y={25 + i * 15} width="30" height="10" rx="1" 
                    fill="#1a202c" stroke="#4a5568" strokeWidth="0.5" />
              {/* LEDs */}
              <circle cx="20" cy={30 + i * 15} r="2" 
                      fill={isOnline ? '#4a9f6e' : '#c45c5c'} 
                      className={isOnline ? 'anim-pulse' : ''} />
              <circle cx="26" cy={30 + i * 15} r="2" 
                      fill={isOnline ? '#4da6a8' : '#5c6370'} />
            </g>
          ))}
        </svg>
      </div>
      
      <div className="node-label">{data.label}</div>
      <div className={`node-conn-status ${isOnline ? 'online' : 'offline'}`}>
        {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
        {isOnline ? 'Online' : 'Offline'}
      </div>
      {data.connections > 0 && (
        <div className="node-connections">{data.connections} CP connected</div>
      )}
      
      <style>{`
        .node-csms {
          padding: 8px;
          border-radius: 8px;
          background: var(--cr-surface);
          border: 2px solid var(--cr-border);
          transition: all 0.2s;
        }
        .node-csms.selected {
          border-color: var(--cr-accent);
          box-shadow: 0 0 0 2px rgba(77, 166, 168, 0.2);
        }
        .node-csms.online {
          border-color: var(--cr-success-dim);
        }
        .node-conn-status {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          font-size: 0.625rem;
          font-weight: 500;
          text-transform: uppercase;
        }
        .node-conn-status.online {
          color: var(--cr-success);
        }
        .node-conn-status.offline {
          color: var(--cr-danger);
        }
        .node-connections {
          text-align: center;
          font-size: 0.6875rem;
          color: var(--cr-text-muted);
        }
      `}</style>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Main Canvas Component
// ═══════════════════════════════════════════════════════════

const nodeTypes = {
  ev: EVNode,
  evse: EVSENode,
  csms: CSMSNode,
}

const initialNodes = [
  {
    id: 'csms-1',
    type: 'csms',
    position: { x: 500, y: 150 },
    data: { label: 'CSMS', status: 'online', connections: 2 },
  },
  {
    id: 'evse-1',
    type: 'evse',
    position: { x: 280, y: 100 },
    data: { label: 'EVCR-001', state: 'Available', power: 0 },
  },
  {
    id: 'evse-2',
    type: 'evse',
    position: { x: 280, y: 250 },
    data: { label: 'EVCR-002', state: 'Available', power: 0 },
  },
  {
    id: 'ev-1',
    type: 'ev',
    position: { x: 80, y: 100 },
    data: { label: 'EV-01', state: 'Idle' },
  },
  {
    id: 'ev-2',
    type: 'ev',
    position: { x: 80, y: 250 },
    data: { label: 'EV-02', state: 'Idle' },
  },
]

const initialEdges = [
  { id: 'e1', source: 'ev-1', target: 'evse-1', animated: false, style: { stroke: '#4a5568', strokeWidth: 2 } },
  { id: 'e2', source: 'ev-2', target: 'evse-2', animated: false, style: { stroke: '#4a5568', strokeWidth: 2 } },
  { id: 'e3', source: 'evse-1', target: 'csms-1', animated: true, style: { stroke: '#4da6a8', strokeWidth: 2 } },
  { id: 'e4', source: 'evse-2', target: 'csms-1', animated: true, style: { stroke: '#4da6a8', strokeWidth: 2 } },
]

export default function TopologyCanvas() {
  const { connectors, connectivity } = useStore()
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Update nodes with real data
  const updatedNodes = useMemo(() => {
    return nodes.map(node => {
      if (node.type === 'evse') {
        const connectorId = node.id === 'evse-1' ? '1' : '2'
        const connectorData = connectors?.[connectorId]
        if (connectorData) {
          return {
            ...node,
            data: {
              ...node.data,
              state: connectorData.state || 'Available',
              power: connectorData.metrics?.power_w || 0,
            }
          }
        }
      }
      if (node.type === 'ev') {
        const connectorId = node.id === 'ev-1' ? '1' : '2'
        const connectorData = connectors?.[connectorId]
        return {
          ...node,
          data: {
            ...node.data,
            state: connectorData?.state === 'Charging' ? 'Charging' : 'Idle',
          }
        }
      }
      if (node.type === 'csms') {
        return {
          ...node,
          data: {
            ...node.data,
            status: connectivity?.ocpp === 'CONNECTED' ? 'online' : 'offline',
          }
        }
      }
      return node
    })
  }, [nodes, connectors, connectivity])

  // Update edges based on charging state
  const updatedEdges = useMemo(() => {
    return edges.map(edge => {
      if (edge.source.startsWith('ev-')) {
        const connectorId = edge.source === 'ev-1' ? '1' : '2'
        const isCharging = connectors?.[connectorId]?.state === 'Charging'
        return {
          ...edge,
          animated: isCharging,
          style: {
            ...edge.style,
            stroke: isCharging ? '#4a9f6e' : '#4a5568',
          }
        }
      }
      return edge
    })
  }, [edges, connectors])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
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

      const position = {
        x: event.clientX - 200,
        y: event.clientY - 100,
      }

      const newNode = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: {
          label: type === 'ev' ? 'New EV' : type === 'evse' ? 'New EVSE' : 'New CSMS',
          state: type === 'ev' ? 'Idle' : 'Available',
        },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes],
  )

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={updatedNodes}
        edges={updatedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.5}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
      >
        <Background 
          color="var(--cr-grid)" 
          gap={20} 
          size={1}
          style={{ background: 'var(--cr-bg-deep)' }}
        />
        <Controls 
          showInteractive={false}
          style={{ 
            background: 'var(--cr-surface)', 
            border: '1px solid var(--cr-border)',
            borderRadius: '6px',
          }}
        />
        <MiniMap 
          nodeColor={(node) => {
            if (node.type === 'csms') return '#2d3748'
            if (node.type === 'evse') return '#4da6a8'
            return '#2c5282'
          }}
          maskColor="rgba(0, 0, 0, 0.6)"
          style={{
            background: 'var(--cr-surface)',
            border: '1px solid var(--cr-border)',
            borderRadius: '6px',
          }}
        />
      </ReactFlow>
    </div>
  )
}
