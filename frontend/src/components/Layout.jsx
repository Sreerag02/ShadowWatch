import { useEffect, useRef, useState } from 'react'
import { ArrowUpRight, Menu, RefreshCw, ShieldCheck, X } from 'lucide-react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
const groups = [
  { label: 'MONITOR', items: [['/', 'Overview'], ['/entities', 'Organizations']] },
  { label: 'ANALYZE', items: [['/findings', 'Findings'], ['/priority-cases', 'Priority cases'], ['/workflow', 'Expected vs observed'], ['/benchmarking', 'Peer benchmarking']] },
  { label: 'REVIEW', items: [['/reports', 'Reports'], ['/audit', 'Audit trail']] },
]
const navigation = groups.flatMap(group => group.items)
export default function Layout() {
  const { health, risk, refresh, reports } = useWorkspace()
  const [menu, setMenu] = useState(false)
  const location = useLocation()
  const main = useRef(null)
  const selected = navigation.find(([path]) => path === '/' ? location.pathname === '/' : location.pathname.startsWith(path))
  const context = reports.find(r => location.pathname.startsWith(`/entities/${r.entity_id}`))
  useEffect(() => { main.current?.focus() }, [location.pathname])
  const connected = health.data?.status === 'ok' && health.data?.database === 'ok'
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to content</a>
    {menu && <button className="nav-overlay" aria-label="Close navigation" onClick={() => setMenu(false)} />}
    <aside className={`sidebar ${menu ? 'open' : ''}`}><Link to="/" className="brand" onClick={() => setMenu(false)}><div className="brand-mark"><ShieldCheck size={22} /></div><div>SHADOWWATCH<small>SUPERVISORY ANALYTICS</small></div></Link>
      <nav aria-label="Main navigation">{groups.map(group => <div className="nav-group" key={group.label}><div className="nav-label">{group.label}</div>{group.items.map(([path, label]) => <NavLink end={path === '/'} to={path} key={path} onClick={() => setMenu(false)}><span>{label}</span>{path === '/findings' && risk.data && <small>{reports.reduce((n, r) => n + r.aggregation.total_findings, 0)}</small>}</NavLink>)}</div>)}</nav>
      <div className="sidebar-bottom"><Link to="/system" className="system-link"><span className={`status-dot ${connected ? 'online' : ''}`} />System status<ArrowUpRight size={14} /></Link><div className="profile">Supervisor workspace<small>Read-only · No sign-in</small></div></div>
    </aside>
    <div className="workspace"><header className="topbar"><div className="topbar-title"><button className="icon-button mobile-toggle" aria-label={menu ? 'Close menu' : 'Open menu'} aria-expanded={menu} onClick={() => setMenu(!menu)}>{menu ? <X size={19} /> : <Menu size={19} />}</button><span className="breadcrumb">Workspace <span>/</span> <strong>{context?.entity_name || selected?.[1] || (location.pathname === '/system' ? 'System status' : 'Evidence review')}</strong></span></div><div className="header-actions"><Link className="connection" to="/system"><span className={`status-dot ${connected ? 'online' : ''}`} />{health.loading ? 'Checking system' : connected ? 'System connected' : 'Connection unavailable'}</Link><button className="button small" onClick={refresh} disabled={risk.loading} aria-label="Refresh data"><RefreshCw size={14} className={risk.loading ? 'spin' : ''} /><span>Refresh</span></button></div></header>
      <main id="main-content" ref={main} tabIndex={-1}><Outlet /></main><footer className="app-footer"><span>ShadowWatch / Supervisory workspace</span><span>Prototype indicators. Evidence requires human review.</span></footer>
    </div></div>
}
