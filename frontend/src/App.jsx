import { useCallback, useEffect, useState } from "react";
import { Activity, AlertTriangle, ShieldCheck, Upload, RefreshCw, Radio, Server, Network, Zap } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function Metric({ icon: Icon, label, value, note, tone = "" }) {
  return <article className="metric"><div className="metric-top"><span>{label}</span><span className={`metric-icon ${tone}`}><Icon size={17}/></span></div><strong>{value}</strong><small>{note}</small></article>;
}

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [m, a, e] = await Promise.all([
        fetch(`${API}/api/metrics`), fetch(`${API}/api/alerts`), fetch(`${API}/api/events?limit=12`)
      ]);
      if (![m, a, e].every(r => r.ok)) throw new Error("API request failed. Is the backend running?");
      const [mj, aj, ej] = await Promise.all([m.json(), a.json(), e.json()]);
      setMetrics(mj); setAlerts(aj.items); setEvents(ej.items); setError("");
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) { setError(err.message); }
  }, []);

  useEffect(() => { refresh(); const timer = setInterval(refresh, 5000); return () => clearInterval(timer); }, [refresh]);

  async function loadDemo() {
    setBusy(true);
    try { const r = await fetch(`${API}/api/events/demo`, { method: "POST" }); if (!r.ok) throw new Error("Could not load demo events"); await refresh(); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    const form = new FormData(); form.append("file", file);
    try { const r = await fetch(`${API}/api/events/upload`, { method: "POST", body: form }); const data = await r.json(); if (!r.ok) throw new Error(data.detail || "Upload failed"); await refresh(); }
    catch (err) { setError(err.message); } finally { setBusy(false); event.target.value = ""; }
  }

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={23}/></div><div><b>CYBERWATCH</b><small>THREAT INTELLIGENCE</small></div></div>
      <div className="side-label">WORKSPACE</div>
      <div className="nav-item active"><Activity size={17}/> Overview</div>
      <div className="nav-item"><AlertTriangle size={17}/> Threat alerts <span className="nav-count">{alerts.length}</span></div>
      <div className="nav-item"><Network size={17}/> Event stream</div>
      <div className="side-bottom"><div className="status-dot"></div><span>Detection engine online</span></div>
    </aside>
    <main className="main">
      <header className="topbar"><div><div className="eyebrow">SECURITY OPERATIONS CENTER / OVERVIEW</div><h1>Threat overview</h1><p>Monitor network activity and investigate suspicious behavior.</p></div><div className="top-actions"><span className="live"><i/> LIVE MONITORING</span><button className="icon-button" onClick={refresh} title="Refresh"><RefreshCw size={17}/></button></div></header>
      {error && <div className="error"><AlertTriangle size={16}/>{error}</div>}
      <section className="metrics">
        <Metric icon={Activity} label="Events analyzed" value={metrics?.total_events ?? "—"} note="Total ingested events" />
        <Metric icon={AlertTriangle} label="Suspicious events" value={metrics?.suspicious_events ?? "—"} note="Flagged by AI and rules" tone="orange"/>
        <Metric icon={Zap} label="Open alerts" value={metrics?.open_alerts ?? "—"} note="Require investigation" tone="red"/>
        <Metric icon={ShieldCheck} label="Detection rate" value={metrics ? `${metrics.detection_rate}%` : "—"} note="Flagged / analyzed" tone="green"/>
      </section>
      <section className="content-grid">
        <article className="panel alerts-panel"><div className="panel-heading"><div><h2>Priority alerts</h2><p>Most recent suspicious activity</p></div><span className="subtle">{alerts.length} TOTAL</span></div>
          {alerts.length === 0 ? <div className="empty"><ShieldCheck size={27}/><b>No alerts yet</b><span>Load demo data or upload a CSV to begin.</span></div> :
            <div className="alert-list">{alerts.slice(0,8).map(a => <div className="alert-row" key={a.id}><span className={`severity ${a.severity}`}></span><div className="alert-copy"><b>{a.title}</b><small>{a.src_ip} · {new Date(a.timestamp).toLocaleString()}</small></div><strong className="risk">{a.risk_score}<small> RISK</small></strong></div>)}</div>}
        </article>
        <article className="panel engine-panel"><div className="panel-heading"><div><h2>Detection engine</h2><p>Model and rule status</p></div><span className="engine-badge"><i/> ACTIVE</span></div>
          <div className="engine-item"><span className="engine-icon"><Zap size={17}/></span><div><b>Isolation Forest</b><small>Unsupervised anomaly detection</small></div><span className="check">READY</span></div>
          <div className="engine-item"><span className="engine-icon"><ShieldCheck size={17}/></span><div><b>Security rule engine</b><small>Brute force · port scan · privilege</small></div><span className="check">READY</span></div>
          <div className="engine-item"><span className="engine-icon"><Server size={17}/></span><div><b>REST API</b><small>FastAPI event ingestion</small></div><span className="check">READY</span></div>
          <div className="engine-foot"><span>Auto refresh: 5 seconds</span><span>Updated {lastUpdated || "—"}</span></div>
        </article>
      </section>
      <section className="panel stream-panel"><div className="panel-heading"><div><h2>Recent event stream</h2><p>Latest normalized security events</p></div><div className="stream-actions"><label className="upload-btn"><Upload size={15}/> Upload CSV<input type="file" accept=".csv" onChange={uploadFile} disabled={busy}/></label><button className="primary-btn" onClick={loadDemo} disabled={busy}><Radio size={15}/>{busy ? "Processing…" : "Load demo events"}</button></div></div>
        {events.length === 0 ? <div className="empty compact">No events ingested yet.</div> : <div className="table-wrap"><table><thead><tr><th>TIME</th><th>SOURCE IP</th><th>DESTINATION</th><th>PROTOCOL</th><th>PACKETS</th><th>AI RESULT</th><th>RISK</th></tr></thead><tbody>{events.map(e => <tr key={e.id}><td>{new Date(e.timestamp).toLocaleTimeString()}</td><td className="mono">{e.src_ip}</td><td className="mono">{e.dst_ip}:{e.dst_port}</td><td>{e.protocol}</td><td>{e.packets}</td><td><span className={e.is_anomaly ? "tag danger" : "tag safe"}>{e.is_anomaly ? "SUSPICIOUS" : "NORMAL"}</span></td><td className="mono">{e.risk_score}</td></tr>)}</tbody></table></div>}
      </section>
      <footer>CYBERWATCH <span>AI-ASSISTED SECURITY MONITORING · DEMO BUILD</span></footer>
    </main>
  </div>;
}
