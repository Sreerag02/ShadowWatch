import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { useApi } from '../hooks/useApi'
import { segment } from '../api/client'
import { Badge, DataGrid, Empty, Facts, Info, PageHeading, Panel, State } from '../components/Common'
import { Components } from '../components/Charts'
import { FindingTable, PriorityTable } from '../components/Tables'
import { EvidenceTree } from '../components/Evidence'
import Benchmark from '../components/Benchmark'
import { number } from '../utils/format'
export function Assets({ entityId }) {
  const { revision, refresh } = useWorkspace()
  const request = useApi(`/entities/${segment(entityId)}/assets`, { revision, pageSize: 1000 })
  return <Panel title="Organization assets" subtitle="Inventory and monitoring expectations supplied by PostgreSQL"><State {...request} retry={refresh}><DataGrid caption="Organization assets" rows={request.data || []} rowKey="asset_id" columns={[{ key: 'asset_name', label: 'Asset', render: a => <><strong>{a.asset_name}</strong><small className="mono">{a.asset_id}</small></> }, { key: 'asset_type', label: 'Type' }, { key: 'criticality', label: 'Criticality', render: a => <Badge value={a.criticality} /> }, { key: 'business_function', label: 'Business function' }, { key: 'monitoring_expected', label: 'Monitoring expected', render: a => a.monitoring_expected == null ? 'Unknown' : a.monitoring_expected ? 'Yes' : 'No' }]} /></State></Panel>
}
export function Contributors({ report }) {
  return <Panel title="What is driving this assessment?" subtitle="Contributors and explanations from the backend"><p className="lead-reason">{report.explanation}</p>{report.top_contributors.length ? <div className="contributor-list">{report.top_contributors.map(c => <Link to={`/findings/${c.finding_ids[0]}`} key={c.rule_id}><span className="rule-tag">{c.rule_id}</span><div><strong>{c.affected_cases} affected cases · {c.affected_assets} assets</strong><p>{c.example_reason}</p></div><span>↗</span></Link>)}</div> : <Empty title="No scored contributors" description="Review available evidence and coverage before interpreting a zero score." />}</Panel>
}
export default function EntityDetails() {
  const { entityId } = useParams()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'overview'
  const { risk, reports, refresh } = useWorkspace()
  const report = reports.find(r => r.entity_id === entityId)
  return <><Link className="back-link" to="/entities">← Organization directory</Link><State {...risk} retry={refresh}>{!report ? <Empty title="Organization not found" /> : <>
    <PageHeading eyebrow={`${report.entity_id} / ${report.sector || 'UNKNOWN SECTOR'}`} title={report.entity_name} description={`Peer group: ${report.peer_group || 'Unavailable'} · Stored organization metadata`} action={<Link className="button" to={`/reports?entity=${entityId}`}>View report →</Link>} />
    <div className="entity-score-banner"><div><span className="eyebrow">OBSERVED SUPERVISORY RISK</span><strong>{number(report.overall_score, 2)}<small>/ 100</small></strong></div><Badge value={report.overall_level} /><div className="score-coverage"><strong>{report.score_status === 'PARTIAL' ? 'Partial component coverage' : 'Component scores available'}</strong><span>{number(report.available_component_weight * 100)}% of configured component weight available</span></div><div><strong>{report.aggregation.total_findings}</strong><span>supervisory findings</span></div></div>
    <div className="tabs" role="tablist" aria-label="Organization sections">{['overview', 'findings', 'priority cases', 'assets', 'benchmark', 'evidence'].map(t => <button role="tab" aria-selected={tab === t} className={tab === t ? 'active' : ''} key={t} onClick={() => setParams({ tab: t })}>{t.replace(/^./, c => c.toUpperCase())}</button>)}</div>
    {tab === 'overview' && <><div className="two-columns"><Panel title="Risk component breakdown" subtitle="Backend scores and their weighted contributions"><Components components={report.components} /></Panel><Panel title="Assessment context"><Facts items={[["Cases", report.denominators.cases], ["Investigated cases", report.denominators.investigated_cases], ["Serious cases", report.denominators.serious_cases], ["Explicitly monitored assets", report.denominators.monitored_assets], ["Affected cases", report.aggregation.affected_cases], ["Affected assets", report.aggregation.affected_assets]]} /><Info>{report.disclaimer}</Info>{report.score_status === 'PARTIAL' && <Info>Unavailable-component upper bound: {number(report.unavailable_component_upper_bound, 2)}. This is not a confidence interval.</Info>}</Panel></div><Contributors report={report} /><Panel title="Data coverage and limitations"><ul className="limitations">{report.limitations.map((text, i) => <li key={i}>{text}</li>)}</ul></Panel></>}
    {tab === 'findings' && <Panel title="Organization findings"><FindingTable findings={report.findings} /></Panel>}
    {tab === 'priority cases' && <Panel title="Case review priorities"><PriorityTable cases={report.priority_cases} /></Panel>}
    {tab === 'assets' && <Assets entityId={entityId} />}
    {tab === 'benchmark' && <Benchmark report={report} />}
    {tab === 'evidence' && <><Panel title="Evidence coverage" subtitle="Record coverage is separate from detector execution status"><EvidenceTree value={report.data_coverage} /><EvidenceTree value={report.engine_status} /></Panel><Panel title="Scoring transparency"><EvidenceTree value={report.components} /><details className="disclosure"><summary>Effective backend configuration</summary><EvidenceTree value={report.config} /></details></Panel></>}
  </>}</State></>
}
