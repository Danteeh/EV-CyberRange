import { X, AlertTriangle, Shield, Target, Wrench, ExternalLink, Clock, Zap } from 'lucide-react'

// CVE Database with detailed information
const CVE_DATABASE = {
  'CVE-2024-11665': {
    id: 'CVE-2024-11665',
    name: 'Hardy Barth cPH2 RCE',
    vendor: 'Hardy Barth',
    product: 'cPH2 / eCB1 Wallbox',
    cvss: 9.8,
    severity: 'CRITICAL',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
    cwe: 'CWE-78: OS Command Injection',
    description: 'The Hardy Barth cPH2 and eCB1 series charging stations contain a critical vulnerability in the diagnostic interface (diag.php). The ping functionality does not properly sanitize user input, allowing remote attackers to execute arbitrary OS commands with root privileges.',
    impact: [
      'Full remote code execution as root',
      'Complete device takeover',
      'Access to stored credentials (MQTT, WiFi, Admin)',
      'Lateral movement to connected infrastructure',
      'Manipulation of charging sessions'
    ],
    exploitation: [
      'Send crafted HTTP request to /cgi-bin/diag.php',
      'Inject shell commands via ping parameter',
      'Commands execute with root privileges',
      'No authentication required'
    ],
    mitigation: [
      'Update firmware to version 1.7.3 or later',
      'Restrict network access to management interface',
      'Place charging stations on isolated VLAN',
      'Implement network monitoring for anomalous requests',
      'Disable diagnostic interface if not needed'
    ],
    references: [
      { title: 'Vendor Advisory', url: 'https://www.hardy-barth.com/security' },
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2024-11665' }
    ],
    published: '2024-03-15',
    port: 8081
  },
  'CVE-2024-11666': {
    id: 'CVE-2024-11666',
    name: 'Hardy Barth Credential Exposure',
    vendor: 'Hardy Barth',
    product: 'cPH2 / eCB1 Wallbox',
    cvss: 7.5,
    severity: 'HIGH',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N',
    cwe: 'CWE-200: Exposure of Sensitive Information',
    description: 'Hardy Barth charging stations expose sensitive configuration data including MQTT broker credentials, WiFi passwords, and admin credentials through an unauthenticated API endpoint.',
    impact: [
      'Exposure of MQTT credentials',
      'WiFi network password disclosure',
      'Admin password leakage',
      'Potential for further attacks using stolen credentials'
    ],
    exploitation: [
      'Access configuration API without authentication',
      'Extract stored credentials from response',
      'Use credentials for lateral movement'
    ],
    mitigation: [
      'Update firmware to latest version',
      'Change all default credentials',
      'Implement network segmentation',
      'Monitor for unauthorized API access'
    ],
    references: [
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2024-11666' }
    ],
    published: '2024-03-15',
    port: 8081
  },
  'CVE-2018-7800': {
    id: 'CVE-2018-7800',
    name: 'Schneider EVlink Hard-coded Credentials',
    vendor: 'Schneider Electric',
    product: 'EVlink Parking / City / Smart Wallbox',
    cvss: 9.8,
    severity: 'CRITICAL',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
    cwe: 'CWE-798: Use of Hard-coded Credentials',
    description: 'Schneider Electric EVlink charging stations contain hard-coded credentials in the firmware that allow attackers to gain administrative access. The credentials cannot be changed by the end user and are the same across all devices of the same model.',
    impact: [
      'Full administrative access to charging station',
      'Ability to modify charging parameters',
      'Access to user data and charging history',
      'Potential for firmware modification',
      'Denial of service by disabling charger'
    ],
    exploitation: [
      'Use publicly known hard-coded credentials',
      'Authenticate to web management interface',
      'Gain full administrative control'
    ],
    mitigation: [
      'Apply firmware update R7 V3.3.0.15 or later',
      'Implement network access controls',
      'Use firewall to restrict management interface access',
      'Monitor for unauthorized login attempts'
    ],
    references: [
      { title: 'Schneider Security Notification', url: 'https://www.se.com/ww/en/download/document/SEVD-2018-354-01/' },
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2018-7800' },
      { title: 'ICS-CERT Advisory', url: 'https://www.cisa.gov/uscert/ics/advisories/ICSA-19-031-01' }
    ],
    published: '2018-12-20',
    port: 8082
  },
  'CVE-2023-32249': {
    id: 'CVE-2023-32249',
    name: 'Wallbox Unauthenticated API Access',
    vendor: 'Wallbox',
    product: 'Pulsar Plus / Commander 2',
    cvss: 8.6,
    severity: 'HIGH',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L',
    cwe: 'CWE-306: Missing Authentication for Critical Function',
    description: 'Wallbox Pulsar Plus and Commander 2 chargers expose a local API that does not require authentication. Attackers on the same network can access sensitive information including WiFi credentials, user data, and charging session details. The API also allows modification of charging parameters.',
    impact: [
      'Access to stored WiFi credentials',
      'Extraction of user account information',
      'Ability to start/stop charging sessions',
      'Modification of charging power limits',
      'Access to charging history and energy data'
    ],
    exploitation: [
      'Discover charger on local network',
      'Access API endpoints without authentication',
      'Extract sensitive configuration data',
      'Manipulate charging sessions'
    ],
    mitigation: [
      'Update to firmware version 5.5.10 or later',
      'Isolate charger on separate network segment',
      'Implement local firewall rules',
      'Disable local API if not needed'
    ],
    references: [
      { title: 'Wallbox Security Advisory', url: 'https://wallbox.com/security' },
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2023-32249' }
    ],
    published: '2023-07-12',
    port: 8083
  },
  'CVE-2022-26132': {
    id: 'CVE-2022-26132',
    name: 'ChargePoint Home Flex DoS',
    vendor: 'ChargePoint',
    product: 'Home Flex',
    cvss: 7.5,
    severity: 'HIGH',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H',
    cwe: 'CWE-400: Uncontrolled Resource Consumption',
    description: 'ChargePoint Home Flex charging stations are vulnerable to a denial of service attack through malformed requests to the local web interface. An attacker can send specially crafted packets that cause the device to become unresponsive, requiring a manual restart.',
    impact: [
      'Charging station becomes unresponsive',
      'Inability to start new charging sessions',
      'Active charging sessions may be interrupted',
      'Manual intervention required to restore service',
      'Potential for repeated attacks causing persistent DoS'
    ],
    exploitation: [
      'Send malformed HTTP requests to web interface',
      'Overflow input buffers with oversized data',
      'Device crashes or becomes unresponsive',
      'Repeat attack to maintain denial of service'
    ],
    mitigation: [
      'Apply latest firmware update from ChargePoint',
      'Implement rate limiting at network level',
      'Use intrusion detection to identify attack patterns',
      'Restrict network access to charger interface'
    ],
    references: [
      { title: 'ChargePoint Advisory', url: 'https://www.chargepoint.com/security' },
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2022-26132' }
    ],
    published: '2022-04-08',
    port: 8084
  },
  'CVE-2024-43659': {
    id: 'CVE-2024-43659',
    name: 'ABB Terra AC Credential Exposure',
    vendor: 'ABB',
    product: 'Terra AC Wallbox',
    cvss: 8.2,
    severity: 'HIGH',
    vector: 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N',
    cwe: 'CWE-522: Insufficiently Protected Credentials',
    description: 'ABB Terra AC Wallbox stores sensitive credentials in plaintext in accessible configuration files. An attacker with network access can retrieve these files and extract OCPP backend credentials, WiFi passwords, and administrative credentials.',
    impact: [
      'Exposure of OCPP backend credentials',
      'WiFi network password disclosure',
      'Administrative credential leakage',
      'Potential compromise of charging network backend',
      'Access to user charging data'
    ],
    exploitation: [
      'Access configuration endpoint via HTTP',
      'Download configuration backup file',
      'Extract plaintext credentials from config',
      'Use credentials to access backend systems'
    ],
    mitigation: [
      'Update to firmware version 1.8.2 or later',
      'Change all default and exposed credentials',
      'Implement TLS for all communications',
      'Restrict access to management interface',
      'Enable configuration file encryption'
    ],
    references: [
      { title: 'ABB Security Advisory', url: 'https://www.abb.com/security' },
      { title: 'NVD Entry', url: 'https://nvd.nist.gov/vuln/detail/CVE-2024-43659' }
    ],
    published: '2024-01-22',
    port: 8085
  },
  'CVE-2025-12357': {
    id: 'CVE-2025-12357',
    name: 'ISO 15118 TLS MITM',
    vendor: 'Generic',
    product: 'ISO 15118 Implementation',
    cvss: 8.1,
    severity: 'HIGH',
    vector: 'CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N',
    cwe: 'CWE-295: Improper Certificate Validation',
    description: 'Multiple ISO 15118 implementations fail to properly validate TLS certificates during the vehicle-to-charger communication handshake. This allows a man-in-the-middle attacker to intercept and modify Plug&Charge authentication data, potentially enabling unauthorized charging or billing fraud.',
    impact: [
      'Interception of Plug&Charge credentials',
      'Modification of charging session parameters',
      'Billing fraud through session manipulation',
      'Theft of vehicle authentication certificates',
      'Impersonation of charging stations or vehicles'
    ],
    exploitation: [
      'Position attacker between vehicle and charger',
      'Perform TLS interception with self-signed cert',
      'Capture Plug&Charge authentication exchange',
      'Modify or replay captured credentials'
    ],
    mitigation: [
      'Implement proper certificate chain validation',
      'Use certificate pinning where possible',
      'Enable mutual TLS authentication',
      'Monitor for certificate anomalies',
      'Implement ISO 15118-20 security improvements'
    ],
    references: [
      { title: 'ISO 15118 Security Analysis', url: 'https://www.iso.org/standard/77845.html' },
      { title: 'Research Paper', url: 'https://arxiv.org/abs/2024.12357' }
    ],
    published: '2025-02-10',
    port: 8086
  }
}

// Get severity color
const getSeverityColor = (severity) => {
  switch (severity) {
    case 'CRITICAL': return '#dc2626'
    case 'HIGH': return '#f97316'
    case 'MEDIUM': return '#eab308'
    case 'LOW': return '#22c55e'
    default: return '#6b7280'
  }
}

// Get CVSS color
const getCVSSColor = (score) => {
  if (score >= 9.0) return '#dc2626'
  if (score >= 7.0) return '#f97316'
  if (score >= 4.0) return '#eab308'
  return '#22c55e'
}

export default function CVEDetailPanel({ cveId, onClose }) {
  const cve = CVE_DATABASE[cveId]
  
  if (!cve) {
    return (
      <div className="cve-panel">
        <div className="cve-header">
          <h3>CVE Not Found</h3>
          <button onClick={onClose} className="close-btn"><X size={18} /></button>
        </div>
        <p style={{ padding: 20, color: 'var(--cr-text-muted)' }}>
          No information available for {cveId}
        </p>
      </div>
    )
  }

  return (
    <div className="cve-panel">
      {/* Header */}
      <div className="cve-header">
        <div className="cve-title-section">
          <span className="cve-id">{cve.id}</span>
          <span 
            className="cve-severity" 
            style={{ background: getSeverityColor(cve.severity) }}
          >
            {cve.severity}
          </span>
        </div>
        <button onClick={onClose} className="close-btn"><X size={18} /></button>
      </div>

      {/* Content */}
      <div className="cve-content">
        {/* Title & Vendor */}
        <div className="cve-main-info">
          <h2 className="cve-name">{cve.name}</h2>
          <div className="cve-vendor">
            <Shield size={14} />
            {cve.vendor} - {cve.product}
          </div>
        </div>

        {/* CVSS Score */}
        <div className="cvss-section">
          <div className="cvss-score" style={{ borderColor: getCVSSColor(cve.cvss) }}>
            <span className="cvss-value" style={{ color: getCVSSColor(cve.cvss) }}>{cve.cvss}</span>
            <span className="cvss-label">CVSS 3.1</span>
          </div>
          <div className="cvss-details">
            <code className="cvss-vector">{cve.vector}</code>
            <div className="cwe-tag">{cve.cwe}</div>
          </div>
        </div>

        {/* Description */}
        <div className="cve-section">
          <h4><AlertTriangle size={14} /> Description</h4>
          <p>{cve.description}</p>
        </div>

        {/* Impact */}
        <div className="cve-section">
          <h4><Zap size={14} /> Impact</h4>
          <ul>
            {cve.impact.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>

        {/* Exploitation */}
        <div className="cve-section">
          <h4><Target size={14} /> Exploitation Steps</h4>
          <ol>
            {cve.exploitation.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>

        {/* Mitigation */}
        <div className="cve-section mitigation">
          <h4><Wrench size={14} /> Mitigation</h4>
          <ul>
            {cve.mitigation.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>

        {/* References */}
        <div className="cve-section">
          <h4><ExternalLink size={14} /> References</h4>
          <div className="references-list">
            {cve.references.map((ref, i) => (
              <a key={i} href={ref.url} target="_blank" rel="noopener noreferrer" className="ref-link">
                {ref.title}
                <ExternalLink size={10} />
              </a>
            ))}
          </div>
        </div>

        {/* Metadata */}
        <div className="cve-meta">
          <span><Clock size={12} /> Published: {cve.published}</span>
          <span>Port: {cve.port}</span>
        </div>
      </div>

      <style>{`
        .cve-panel {
          width: 420px;
          height: 100%;
          background: var(--cr-surface);
          border-left: 1px solid var(--cr-border);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        
        .cve-header {
          padding: 16px;
          background: var(--cr-surface2);
          border-bottom: 1px solid var(--cr-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .cve-title-section {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .cve-id {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--cr-text);
        }
        
        .cve-severity {
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 0.65rem;
          font-weight: 700;
          color: white;
          letter-spacing: 0.05em;
        }
        
        .close-btn {
          background: transparent;
          border: none;
          color: var(--cr-text-muted);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
        }
        .close-btn:hover {
          background: var(--cr-surface3);
          color: var(--cr-text);
        }
        
        .cve-content {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }
        
        .cve-main-info {
          margin-bottom: 16px;
        }
        
        .cve-name {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--cr-text);
          margin: 0 0 8px 0;
        }
        
        .cve-vendor {
          display: flex;
          align-items: center;
          gap: 6px;
          color: var(--cr-text-muted);
          font-size: 0.8rem;
        }
        
        .cvss-section {
          display: flex;
          gap: 16px;
          align-items: center;
          padding: 12px;
          background: var(--cr-bg-deep);
          border-radius: 8px;
          margin-bottom: 16px;
        }
        
        .cvss-score {
          width: 60px;
          height: 60px;
          border: 3px solid;
          border-radius: 50%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .cvss-value {
          font-size: 1.3rem;
          font-weight: 700;
          line-height: 1;
        }
        
        .cvss-label {
          font-size: 0.55rem;
          color: var(--cr-text-muted);
          margin-top: 2px;
        }
        
        .cvss-details {
          flex: 1;
        }
        
        .cvss-vector {
          font-size: 0.65rem;
          color: var(--cr-text-dim);
          background: var(--cr-surface);
          padding: 4px 8px;
          border-radius: 4px;
          display: block;
          margin-bottom: 8px;
          word-break: break-all;
        }
        
        .cwe-tag {
          font-size: 0.7rem;
          color: var(--cr-text-muted);
        }
        
        .cve-section {
          margin-bottom: 16px;
        }
        
        .cve-section h4 {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--cr-text-secondary);
          margin: 0 0 8px 0;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .cve-section p {
          font-size: 0.85rem;
          color: var(--cr-text-muted);
          line-height: 1.6;
          margin: 0;
        }
        
        .cve-section ul, .cve-section ol {
          margin: 0;
          padding-left: 20px;
        }
        
        .cve-section li {
          font-size: 0.8rem;
          color: var(--cr-text-muted);
          line-height: 1.8;
        }
        
        .cve-section.mitigation {
          background: rgba(34, 197, 94, 0.05);
          border: 1px solid rgba(34, 197, 94, 0.2);
          border-radius: 8px;
          padding: 12px;
        }
        
        .cve-section.mitigation h4 {
          color: #22c55e;
        }
        
        .references-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        
        .ref-link {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.8rem;
          color: var(--cr-accent);
          text-decoration: none;
        }
        .ref-link:hover {
          text-decoration: underline;
        }
        
        .cve-meta {
          display: flex;
          justify-content: space-between;
          padding-top: 12px;
          border-top: 1px solid var(--cr-border);
          font-size: 0.7rem;
          color: var(--cr-text-dim);
        }
        
        .cve-meta span {
          display: flex;
          align-items: center;
          gap: 4px;
        }
      `}</style>
    </div>
  )
}

// Export CVE database for use in other components
export { CVE_DATABASE }
