import { Link } from 'react-router-dom'
import { Info, Panel, Facts } from './Common'
import { human, number, time } from '../utils/format'
export function EvidenceTree({ value, name = 'Evidence', depth = 0 }) {
  if (value === null || value === undefined) return <span className="muted">Not recorded</span>
  if (typeof value !== 'object') return <span className="evidence-value">{typeof value === 'boolean' ? value ? 'Yes' : 'No' : String(value)}</span>
  const entries = Object.entries(value)
  if (!entries.length) return <span className="muted">No records supplied</span>
  return <div className="evidence-tree">{entries.map(([key, item]) => <div className="evidence-entry" key={key}>{item && typeof item === 'object' ? <details open={depth === 0 && entries.length < 6}><summary>{Array.isArray(value) ? `${name} ${Number(key) + 1}` : human(key)} <small>{Array.isArray(item) ? `${item.length} records` : `${Object.keys(item).length} fields`}</small></summary><EvidenceTree value={item} name={human(key)} depth={depth + 1} /></details> : <><span className="evidence-key">{human(key)}</span><EvidenceTree value={item} depth={depth + 1} /></>}</div>)}</div>
}
export function BehaviourEvidence({ finding }) {
  const e = finding.evidence || {}
  if (finding.rule_id === 'R006') return <Panel title="Investigation note similarity" subtitle="Offline TF-IDF cosine similarity · Review cue, not proof of misconduct"><Facts items={[["Similarity", e.similarity_score == null ? null : `${number(e.similarity_score * 100, 1)}%`], ["Threshold", e.similarity_threshold == null ? null : `${number(e.similarity_threshold * 100, 1)}%`], ["Distinct cases", e.repetition_count], ["Investigation", e.investigation_id]]} /><blockquote>{e.note_excerpt || 'No note excerpt supplied.'}</blockquote><h3 className="inset-title">Compared cases</h3><div className="case-links">{(e.case_ids || '').split(', ').filter(Boolean).map(id => <Link key={id} to={`/cases/${id}`}>{id}</Link>)}</div><Info>The supplied excerpt belongs to the focal investigation. Open a compared case to inspect its actual notes.</Info></Panel>
  if (finding.rule_id === 'R007') return <Panel title="Investigation duration comparison" subtitle="Actual investigation timestamps, relative to the backend peer baseline"><div className="duration-comparison"><div><span>Observed duration</span><strong>{number(e.duration_minutes, 2)} <small>min</small></strong></div><div><span>Relevant baseline</span><strong>{number(e.baseline_duration_minutes, 2)} <small>min</small></strong></div></div><Facts items={[["Direction", e.direction], ["Ratio", number(e.duration_ratio, 3)], ["Baseline cases", e.baseline_case_count], ["Category", e.category]]} /></Panel>
  if (finding.rule_id === 'R008') return <Panel title="Recurring incident window" subtitle="Distinct linked alerts for the same asset and category"><Facts items={[["Asset", e.asset_id || finding.asset_id], ["Category", e.category], ["Distinct alerts", e.incident_count], ["Span (days)", number(e.time_span_days, 2)], ["First timestamp", time(e.first_timestamp)], ["Last timestamp", time(e.last_timestamp)]]} /><div className="case-links">{(e.case_ids || '').split(', ').filter(Boolean).map(id => <Link key={id} to={`/cases/${id}`}>{id}</Link>)}</div></Panel>
  if (finding.rule_id === 'R009') return <Panel title="Combined behavioural indicators" subtitle="The backend preserves every contributing indicator; this is not an opaque score"><Facts items={[["Contributing rules", e.triggered_rules], ["Rule count", e.rule_count]]} /><EvidenceTree value={e.evidence || e} /></Panel>
  return null
}
