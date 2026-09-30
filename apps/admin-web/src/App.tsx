type MetricCardProps = {
  label: string
  value: string
  trend: string
}

function MetricCard({ label, value, trend }: MetricCardProps) {
  return (
    <div className="metric-card">
      <p>{label}</p>
      <h3>{value}</h3>
      <span>{trend}</span>
    </div>
  )
}

function App() {
  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">TM</span>
          <div>
            <strong>TravelMate</strong>
            <small>Admin Console</small>
          </div>
        </div>

        <nav>
          <a href="#">Dashboard</a>
          <a href="#">Users</a>
          <a href="#">Verification</a>
          <a href="#">Moderation</a>
          <a href="#">Trips</a>
          <a href="#">Payments</a>
          <a href="#">Security</a>
          <a href="#">Settings</a>
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Operations overview</p>
            <h1>Control center</h1>
          </div>
          <button type="button">Export report</button>
        </header>

        <section className="metrics-grid">
          <MetricCard label="Active users" value="128.4K" trend="+12.8%" />
          <MetricCard label="Verified profiles" value="74.1%" trend="+3.1%" />
          <MetricCard label="Open appeals" value="214" trend="-8.2%" />
          <MetricCard label="Revenue" value="₹9.8L" trend="+16.4%" />
        </section>

        <section className="content-grid">
          <div className="panel">
            <h2>Priority queues</h2>
            <ul className="task-list">
              <li><span>Verification</span><strong>42 pending</strong></li>
              <li><span>Moderation</span><strong>18 urgent</strong></li>
              <li><span>Chargebacks</span><strong>6 review</strong></li>
              <li><span>Support tickets</span><strong>31 open</strong></li>
            </ul>
          </div>

          <div className="panel">
            <h2>Compliance posture</h2>
            <ul className="task-list">
              <li><span>Privacy controls</span><strong>Healthy</strong></li>
              <li><span>Consent tracking</span><strong>Synced</strong></li>
              <li><span>Backup DR</span><strong>Verified</strong></li>
              <li><span>Security audit</span><strong>Current</strong></li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
