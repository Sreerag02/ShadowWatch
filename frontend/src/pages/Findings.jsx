import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { Filter, Info, PageHeading, Panel, SearchBox, State } from '../components/Common'
import { FindingTable } from '../components/Tables'
export default function Findings() {
  const { risk, findings, reports, refresh } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(''), [severity, setSeverity] = useState(''), [rule, setRule] = useState(''), [problem, setProblem] = useState(''), [review, setReview] = useState('')
  const entity = params.get('entity') || ''
  const rows = findings.filter(f => (!entity || f.entity_id === entity) && (!severity || f.severity === severity) && (!rule || f.rule_id === rule) && (!problem || f.problem_type === problem) && `${f.rule_id} ${f.reason} ${f.case_id || ''} ${f.asset_id || ''}`.toLowerCase().includes(query.toLowerCase()))
  return <><PageHeading title="Findings" description="Trace every supervisory indicator to its supporting operational evidence." /><State {...risk} retry={refresh}><Panel title="Finding register" subtitle={`${findings.length} backend findings · Human decisions are not yet persisted`}><div className="toolbar"><SearchBox value={query} onChange={setQuery} label="Search findings" placeholder="Search reason, case or asset…" /><Filter label="Organization" value={entity} onChange={v => setParams(v ? { entity: v } : {})} options={reports.map(r => ({ value: r.entity_id, label: r.entity_name }))} /><Filter label="Severity" value={severity} onChange={setSeverity} options={['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']} /><Filter label="Rule" value={rule} onChange={setRule} options={[...new Set(findings.map(f => f.rule_id))].sort().map(v => ({ value: v, label: v }))} /><Filter label="Problem type" value={problem} onChange={setProblem} options={[...new Set(findings.map(f => f.problem_type))].sort()} /><Filter label="Review status" value={review} onChange={setReview} options={[{ value: 'unavailable', label: 'Unavailable (all records)' }]} /></div><FindingTable findings={rows} /></Panel><Info>Assessment labels such as “Confirmed gap” come from the analytics engine. They are not a supervisor’s confirmation. Persisted review status is unavailable.</Info></State></>
}
