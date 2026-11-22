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
  const [noteDrafts, setNoteDrafts] = useState({});
  const [assigneeDrafts, setAssigneeDrafts] = useState({});
  const [alertStatusFilter, setAlertStatusFilter] = useState("all");
  const [alertSeverityFilter, setAlertSeverityFilter] = useState("all");

  const refresh = useCallback(async () => {
    try {
      const alertParams = new URLSearchParams();
      if (alertStatusFilter !== "all") alertParams.set("status", alertStatusFilter);
      if (alertSeverityFilter !== "all") alertParams.set("severity", alertSeverityFilter);
      const [m, a, e] = await Promise.all([
        fetch(`${API}/api/metrics`),
        fetch(`${API}/api/alerts?${alertParams.toString()}`),
        fetch(`${API}/api/events?limit=12`)
      ]);
      if (![m, a, e].every(r => r.ok)) throw new Error("API request failed. Is the backend running?");
      const [mj, aj, ej] = await Promise.all([m.json(), a.json(), e.json()]);
      setMetrics(mj); setAlerts(aj.items); setEvents(ej.items); setError("");
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) { setError(err.message); }
  }, [alertStatusFilter, alertSeverityFilter]);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    let socket;
    try {
      socket = new WebSocket(`${API.replace(/^http/, "ws")}/ws/events`);
      socket.onmessage = () => refresh();
    } catch {
      // Five-second polling remains available if WebSocket is unavailable.
    }
    return () => {
      clearInterval(timer);
      socket?.close();
    };
  }, [refresh]);

  async function updateAlert(alertId, status) {
    try {
      const response = await fetch(`${API}/api/alerts/${alertId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Could not update alert");
      }
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function addAlertNote(alertId) {
    const text = (noteDrafts[alertId] || "").trim();
    if (!text) return;
    try {
      const response = await fetch(`${API}/api/alerts/${alertId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not save investigation note");
      setNoteDrafts(current => ({ ...current, [alertId]: "" }));
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function assignAlert(alertId, assignee) {
    try {
      const response = await fetch(`${API}/api/alerts/${alertId}/assignee`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assignee }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not update alert assignment");
      setAssigneeDrafts(current => ({ ...current, [alertId]: "" }));
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

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
        <article className="panel alerts-panel"><div className="panel-heading"><div><h2>Priority alerts</h2><p>Most recent suspicious activity</p></div><div className="alert-filters"><select aria-label="Filter alerts by status" value={alertStatusFilter} onChange={event => setAlertStatusFilter(event.target.value)}><option value="all">All statuses</option><option value="open">Open</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option></select><select aria-label="Filter alerts by severity" value={alertSeverityFilter} onChange={event => setAlertSeverityFilter(event.target.value)}><option value="all">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><span className="subtle">{alerts.length} SHOWN</span></div></div>
          {alerts.length === 0 ? <div className="empty"><ShieldCheck size={27}/><b>No alerts yet</b><span>Load demo data or upload a CSV to begin.</span></div> :
            <div className="alert-list">{alerts.slice(0,8).map(a => <div className="alert-row" key={a.id}><span className={`severity ${a.severity}`}></span><div className="alert-copy"><b>{a.title}</b><small>{a.src_ip} · {new Date(a.timestamp).toLocaleString()}</small><span className={`alert-status ${a.status}`}>{a.status}</span><details className="alert-notes"><summary>Investigation notes ({a.notes?.length ?? 0})</summary>{(a.notes || []).map((note, index) => <p key={index}>{note.text}<small>{new Date(note.created_at).toLocaleString()}</small></p>)}<div className="note-entry"><input aria-label="Investigation note" placeholder="Add an investigation note" maxLength={1000} value={noteDrafts[a.id] || ""} onChange={event => setNoteDrafts(current => ({ ...current, [a.id]: event.target.value }))}/><button onClick={() => addAlertNote(a.id)} disabled={!(noteDrafts[a.id] || "").trim()}>Add note</button></div></details><details className="alert-assignment"><summary>Owner: {a.assignee || "Unassigned"}</summary><div className="note-entry"><input aria-label="Alert assignee" placeholder="Analyst name" maxLength={80} value={assigneeDrafts[a.id] || ""} onChange={event => setAssigneeDrafts(current => ({ ...current, [a.id]: event.target.value }))}/><button onClick={() => assignAlert(a.id, assigneeDrafts[a.id])} disabled={!(assigneeDrafts[a.id] || "").trim()}>Assign</button><button onClick={() => assignAlert(a.id, null)}>Clear</button></div></details></div><strong className="risk">{a.risk_score}<small> RISK</small></strong><div className="alert-actions">{a.status === "open" && <button onClick={() => updateAlert(a.id, "acknowledged")}>Acknowledge</button>}{a.status !== "resolved" && <button onClick={() => updateAlert(a.id, "resolved")}>Resolve</button>}</div></div>)}</div>}
        </article>
        <article className="panel engine-panel"><div className="panel-heading"><div><h2>Detection engine</h2><p>Model and rule status</p></div><span className="engine-badge"><i/> ACTIVE</span></div>
          <div className="engine-item"><span className="engine-icon"><Zap size={17}/></span><div><b>Isolation Forest</b><small>Unsupervised anomaly detection</small></div><span className="check">READY</span></div>
          <div className="engine-item"><span className="engine-icon"><ShieldCheck size={17}/></span><div><b>Security rule engine</b><small>Brute force · port scan · privilege</small></div><span className="check">READY</span></div>
          <div className="engine-item"><span className="engine-icon"><Server size={17}/></span><div><b>REST API</b><small>FastAPI + WebSocket event stream</small></div><span className="check">READY</span></div>
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
