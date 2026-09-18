import { Link, useParams } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { useApi } from '../hooks/useApi'
import { segment } from '../api/client'
import { Badge, Empty, Facts, Info, PageHeading, Panel, State } from '../components/Common'
import { EvidenceTree } from '../components/Evidence'
import { FindingTable } from '../components/Tables'
import Workflow from '../components/Workflow'
import { human, number, time } from '../utils/format'
function CaseAsset({ entityId, assetId }) {
  const { revision, refresh } = useWorkspace()
  const request = useApi(assetId ? `/entities/${segment(entityId)}/assets` : null, { revision, pageSize: 1000 })
  const asset = request.data?.find(a => a.asset_id === assetId)
  return <Panel title="Linked asset"><State {...request} retry={refresh}>{asset ? <EvidenceTree value={asset} /> : <Empty title="No linked asset record" description="The case does not provide a matching asset in the organization inventory." />}</State></Panel>
}
function Timeline({ data }) {
  const events = [{ label: 'Alert recorded', value: data.alert?.timestamp, id: data.alert_id }, { label: 'Case opened', value: data.opened_at, id: data.case_id }, ...data.investigations.flatMap(i => [{ label: 'Investigation started', value: i.started_at, id: i.investigation_id }, { label: 'Investigation completed', value: i.completed_at, id: i.investigation_id }]), ...data.escalations.map(e => ({ label: 'Escalation timestamp', value: e.escalated_at, id: e.escalation_id })), { label: 'Case closed', value: data.closed_at, id: data.case_id }]
  const dated = events.filter(e => e.value).sort((a, b) => Date.parse(a.value) - Date.parse(b.value))
  const missing = events.filter(e => !e.value)
  if (!data.investigations.length) missing.push({ label: 'Investigation record', id: 'No investigation' })
  if (!data.escalations.length) missing.push({ label: 'Escalation record', id: 'No escalation' })
  return <Panel title="Recorded case timeline" subtitle="Chronological timestamps as recorded; a timestamp alone does not prove an action occurred"><ol className="timeline">{dated.map((event, i) => <li key={i}><div className="timeline-node" /><div><strong>{event.label}</strong><span className="mono">{time(event.value)}</span><small>{event.id}</small></div></li>)}</ol>{missing.length > 0 && <div className="missing-stages"><strong>Missing or unrecorded stages</strong>{missing.map((event, i) => <div key={i}>{event.label}<span>{event.id} · Not recorded</span></div>)}</div>}</Panel>
}
export default function CaseDetails() {
  const { caseId } = useParams()
  const { revision, refresh, risk, priorities, findings, entityName } = useWorkspace()
  const request = useApi(`/cases/${segment(caseId)}`, { revision })
  const data = request.data
  const priority = priorities.find(p => p.case_id === caseId)
  const normalized = findings.filter(f => f.case_id === caseId)
  return <><Link className="back-link" to="/priority-cases">← Priority review queue</Link><State {...request} retry={refresh}>{data && <>
    <PageHeading eyebrow={`${data.entity_id} / CASE INVESTIGATION`} title={data.case_id} description={`${entityName(data.entity_id)} · ${human(data.alert?.category)}`} action={<Badge value={data.alert?.severity} />} />
    <div className="case-summary-strip"><div><small>CASE STATUS</small><strong>{human(data.status)}</strong></div><div><small>REVIEW PRIORITY</small><strong>{priority ? `${number(priority.priority_score, 2)} / 100` : risk.loading ? 'Loading…' : 'Unavailable'}</strong>{priority && <Badge value={priority.priority_level} />}</div><div><small>ANALYST</small><strong>{data.analyst_id || 'Not recorded'}</strong></div><div><small>LINKED FINDINGS</small><strong>{risk.loading ? 'Loading…' : risk.error ? 'Unavailable' : normalized.length}</strong></div></div>
    <Workflow workflow={data.workflow} />
    <div className="detail-grid"><div><Panel title="Case and alert evidence"><Facts items={[["Case opened", time(data.opened_at)], ["Case closed", time(data.closed_at)], ["Resolution", data.resolution], ["Closure reason", data.closure_reason]]} /><EvidenceTree value={data.alert} name="Alert" /></Panel><Panel title="Investigations" subtitle={`${data.investigations.length} source records; all linked records retained`}><EvidenceTree value={data.investigations} name="Investigation" /></Panel><Panel title="Escalations" subtitle={`${data.escalations.length} source records; flags and timestamps shown independently`}><EvidenceTree value={data.escalations} name="Escalation" /></Panel><CaseAsset entityId={data.entity_id} assetId={data.alert?.asset_id} /></div><aside><Timeline data={data} /><Panel title="Priority rationale"><State {...risk} retry={refresh}>{priority ? <><p className="lead-reason">{priority.reason}</p><details className="disclosure"><summary>Backend priority breakdown</summary><EvidenceTree value={priority.score_breakdown} /></details></> : <Info>No priority result is available for this case.</Info>}</State></Panel></aside></div>
    <Panel title="Triggered supervisory findings" subtitle="Includes normalized findings and additional Workflow Auditor gaps"><State {...risk} retry={refresh}><FindingTable findings={normalized} compact /></State></Panel>
  </>}</State></>
}
