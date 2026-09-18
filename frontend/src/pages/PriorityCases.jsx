import { useState } from 'react'
import { useWorkspace } from '../context/workspace'
import { Filter, PageHeading, Panel, SearchBox, State } from '../components/Common'
import { PriorityTable } from '../components/Tables'
export default function PriorityCases() {
  const { risk, reports, priorities, refresh } = useWorkspace()
  const [query, setQuery] = useState(''), [entity, setEntity] = useState(''), [level, setLevel] = useState('')
  const rows = priorities.filter(c => (!entity || c.entity_id === entity) && (!level || c.priority_level === level) && `${c.case_id} ${c.reason}`.toLowerCase().includes(query.toLowerCase()))
  return <><PageHeading title="Priority cases" description="Cases ordered by supervisory review priority." /><State {...risk} retry={refresh}><Panel title="Supervisor review queue" subtitle="Case priority is distinct from organization risk"><div className="toolbar"><SearchBox value={query} onChange={setQuery} label="Search cases" placeholder="Search case or rationale…" /><Filter label="Organization" value={entity} onChange={setEntity} options={reports.map(r => ({ value: r.entity_id, label: r.entity_name }))} /><Filter label="Priority level" value={level} onChange={setLevel} options={['LOW', 'MODERATE', 'HIGH', 'CRITICAL']} /></div><PriorityTable cases={rows} /></Panel></State></>
}
