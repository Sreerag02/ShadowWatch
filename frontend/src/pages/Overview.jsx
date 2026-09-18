import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { Empty, Metric, PageHeading, Panel, State, TextLink } from '../components/Common'
import { RiskChart, SeverityChart } from '../components/Charts'
import { OrganizationTable, PriorityTable } from '../components/Tables'
import { isHigh, number } from '../utils/format'
export default function Overview() {
  const { risk, reports, findings, priorities, refresh } = useWorkspace()
  const urgent = priorities.filter(p => isHigh(p.priority_level))
  return <><PageHeading title="Supervisory overview" description="Organization risk, evidence coverage and review priorities." action={<Link className="button primary" to="/priority-cases">Open review queue<ArrowRight size={16} /></Link>} />
    <State {...risk} retry={refresh}>{reports.length === 0 ? <Empty title="No organizations available" description="Import organization records through the backend to begin supervision." /> : <>
      <div className="snapshot-label">CURRENT ASSESSMENT<span>Fetched {risk.fetchedAt?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
      <div className="metric-grid"><Metric label="Organizations" value={number(reports.length)} hint="Across registered sectors" /><Metric label="With review indicators" value={number(reports.filter(r => r.aggregation.total_findings > 0).length)} hint="At least one supervisory finding" /><Metric label="Supervisory findings" value={number(findings.length)} hint="Includes additional workflow gaps" /><Metric label="High / critical cases" value={number(urgent.length)} hint="Backend-assigned review priority" /></div>
      <div className="overview-charts"><Panel title="Organization risk landscape" subtitle="Observed supervisory risk · 0–100" action={<TextLink to="/entities">Explore organizations</TextLink>}><RiskChart reports={reports} /></Panel><Panel title="Finding severity" subtitle="Current assessment, including workflow gaps"><SeverityChart findings={findings} /></Panel></div>
      <div className="signal-strip"><div><strong>{number(findings.filter(f => isHigh(f.severity)).length)}</strong><span>high / critical findings</span></div><div><strong>{number(findings.filter(f => f.rule_id === 'R005').length)}</strong><span>monitoring blind-spot episodes</span></div><div><strong>{number(findings.filter(f => f.source_engine === 'behaviour_analytics').length)}</strong><span>behaviour indicators</span></div></div>
      <Panel title="Organization watchlist" subtitle="Read risk together with evidence and data coverage" action={<TextLink to="/entities">All organizations</TextLink>}><OrganizationTable reports={reports} /></Panel>
      <Panel title="Priority review queue" subtitle="Highest backend priorities across organizations" action={<TextLink to="/priority-cases">Full queue</TextLink>}><PriorityTable cases={priorities.slice(0, 5)} compact /></Panel>
    </>}</State></>
}
