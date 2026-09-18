import { useState } from 'react'
import { AlertCircle, ArrowUpRight, ChevronLeft, ChevronRight, Database, LoaderCircle, Search, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { human, number } from '../utils/format'

export function Badge({ value, children }) { return <span className={`badge badge-${String(value || 'unknown').toLowerCase()}`}>{children || human(value)}</span> }
export function PageHeading({ eyebrow = 'SUPERVISORY WORKSPACE', title, description, action }) { return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div> }
export function Panel({ title, subtitle, action, children, className = '' }) { return <section className={`panel ${className}`}><div className="panel-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section> }
export function State({ loading, error, retry, children }) {
  if (loading) return <div className="state loading" role="status"><LoaderCircle className="spin" size={26} /><h3>Loading supervisory data</h3><p>Reading the latest assessment from the backend.</p></div>
  if (error) return <div className="state error" role="alert"><AlertCircle size={28} /><h3>Data could not be loaded</h3><p>{error}</p>{retry && <button className="button" onClick={retry}>Retry connection</button>}</div>
  return children
}
export function Empty({ title = 'No matching records', description = 'Adjust the filters or refresh the current data.', icon: Icon = Database }) { return <div className="state empty"><Icon size={30} /><h3>{title}</h3><p>{description}</p></div> }
export function Metric({ label, value, hint, icon: Icon = ShieldCheck, tone = '' }) { return <div className={`metric ${tone}`}><div className="metric-label">{label}<Icon size={18} /></div><div className="metric-value">{value}</div><div className="metric-hint">{hint}</div></div> }
export function SearchBox({ value, onChange, placeholder = 'Search records…', label = 'Search' }) { return <label className="search-box"><Search size={16} /><span className="sr-only">{label}</span><input aria-label={label} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} /></label> }
export function Filter({ label, value, onChange, options, all = 'All' }) { return <label className="filter"><span>{label}</span><select aria-label={label} value={value} onChange={e => onChange(e.target.value)}><option value="">{all}</option>{options.map(o => <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>{typeof o === 'string' ? human(o) : o.label}</option>)}</select></label> }
export function Info({ children }) { return <div className="info-note"><AlertCircle size={16} /><div>{children}</div></div> }
export function TextLink({ to, children }) { return <Link className="text-link" to={to}>{children}<ArrowUpRight size={14} /></Link> }
export function DataGrid({ rows, columns, rowKey = 'id', pageSize = 12, emptyTitle, caption = 'Records' }) {
  const [requestedPage, setPage] = useState(0)
  const pages = Math.max(1, Math.ceil(rows.length / pageSize))
  const page = Math.min(requestedPage, pages - 1)
  if (!rows.length) return <Empty title={emptyTitle} />
  return <><div className="table-scroll" tabIndex={0} aria-label={`${caption} table`}><table><caption className="sr-only">{caption}</caption><thead><tr>{columns.map(c => <th key={c.key} scope="col">{c.label}</th>)}</tr></thead><tbody>{rows.slice(page * pageSize, (page + 1) * pageSize).map((row, i) => <tr key={row[rowKey] || i}>{columns.map(c => <td key={c.key} className={c.className || ''}>{c.render ? c.render(row) : row[c.key] ?? '—'}</td>)}</tr>)}</tbody></table></div><div className="pagination"><span>{number(page * pageSize + 1)}–{number(Math.min((page + 1) * pageSize, rows.length))} of {number(rows.length)} records</span><div><button aria-label="Previous page" disabled={page === 0} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></button><span>{page + 1} / {pages}</span><button aria-label="Next page" disabled={page === pages - 1} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></button></div></div></>
}
export function Facts({ items }) { return <dl className="facts">{items.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? 'Not recorded'}</dd></div>)}</dl> }
