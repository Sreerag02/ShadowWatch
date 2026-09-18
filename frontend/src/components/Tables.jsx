import { Link } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { useApi } from '../hooks/useApi'
import { segment } from '../api/client'
import { Badge, DataGrid, TextLink } from './Common'
import { human, isHigh, number } from '../utils/format'

export function OrganizationTable({ reports }) {
  return <DataGrid caption="Organizations" rows={reports} rowKey="entity_id" columns={[
    { key: 'entity_name', label: 'Organization', render: r => <Link className="organization-cell" to={`/entities/${r.entity_id}`}><span><strong>{r.entity_name}</strong><small>{r.entity_id}</small></span></Link> },
    { key: 'sector', label: 'Sector / peer group', render: r => <><span>{r.sector || 'Unknown'}</span><small>{r.peer_group || 'No stored peer group'}</small></> },
    { key: 'overall_score', label: 'Risk score', className: 'numeric', render: r => <span className="score-number">{number(r.overall_score, 2)}<small>/ 100</small></span> },
    { key: 'overall_level', label: 'Risk level', render: r => <Badge value={r.overall_level} /> },
    { key: 'findings', label: 'Findings', className: 'numeric', render: r => number(r.aggregation.total_findings) },
    { key: 'priority', label: 'High / critical cases', className: 'numeric', render: r => number(r.priority_cases.filter(p => isHigh(p.priority_level)).length) },
    { key: 'status', label: 'Score coverage', render: r => <Badge value={r.score_status}>{r.score_status === 'PARTIAL' ? 'Partial' : 'Available'}</Badge> },
    { key: 'open', label: '', render: r => <TextLink to={`/entities/${r.entity_id}`}>View</TextLink> },
  ]} />
}
export function FindingTable({ findings, compact = false }) {
  const { entityName } = useWorkspace()
  const columns = [
    { key: 'severity', label: 'Severity', render: f => <Badge value={f.severity} /> },
    { key: 'rule', label: 'Rule / problem', render: f => <Link className="finding-name" to={`/findings/${f.finding_id}`}><span className="rule-tag">{f.rule_id}</span><strong>{human(f.problem_type)}</strong></Link> },
    ...(!compact ? [{ key: 'entity', label: 'Organization', render: f => <Link to={`/entities/${f.entity_id}`}>{entityName(f.entity_id)}</Link> }, { key: 'case', label: 'Case / asset', render: f => <><span>{f.case_id ? <Link className="mono" to={`/cases/${f.case_id}`}>{f.case_id}</Link> : 'Asset-scoped'}</span><small className="mono">{f.asset_id || 'No linked asset'}</small></> }] : []),
    { key: 'reason', label: 'Evidence / reason', className: 'reason-cell', render: f => <><span className="clamp" title={f.reason}>{f.reason}</span><small>{human(f.assessment)}</small></> },
    ...(!compact ? [{ key: 'source', label: 'Source', render: f => human(f.source_engine || f.source) }, { key: 'review', label: 'Review status', render: () => <span className="muted" title="The backend does not yet store reviewer decisions">Unavailable</span> }] : []),
    { key: 'open', label: '', render: f => <TextLink to={`/findings/${f.finding_id}`}>Evidence</TextLink> },
  ]
  return <DataGrid rows={findings} columns={columns} rowKey="finding_id" caption="Supervisory findings" />
}
function AlertContext({ caseId }) {
  const { revision } = useWorkspace()
  const request = useApi(`/cases/${segment(caseId)}`, { revision })
  if (request.loading) return <span className="muted">Loading alert…</span>
  if (request.error) return <span className="cell-error" title={request.error}>Alert details unavailable</span>
  return <><Badge value={request.data?.alert?.severity} /><small>{human(request.data?.alert?.category)}</small></>
}
export function PriorityTable({ cases, compact = false }) {
  const { entityName } = useWorkspace()
  return <DataGrid rows={cases} rowKey="case_id" pageSize={compact ? 5 : 10} caption="Case review priorities" columns={[
    { key: 'priority', label: 'Priority', render: c => <Badge value={c.priority_level} /> },
    { key: 'case', label: 'Case', render: c => <><Link className="mono strong" to={`/cases/${c.case_id}`}>{c.case_id}</Link><small>{entityName(c.entity_id)}</small></> },
    ...(!compact ? [{ key: 'alert', label: 'Alert severity / category', render: c => <AlertContext caseId={c.case_id} /> }] : []),
    { key: 'findings', label: 'Findings', className: 'numeric', render: c => c.triggered_findings.length },
    { key: 'score', label: 'Score', className: 'numeric', render: c => <strong className="score-number">{number(c.priority_score, 2)}</strong> },
    { key: 'reason', label: 'Review rationale', className: 'reason-cell', render: c => <span className="clamp" title={c.reason}>{c.reason}</span> },
    { key: 'open', label: '', render: c => <TextLink to={`/cases/${c.case_id}`}>Review case</TextLink> },
  ]} />
}
