import { useState } from 'react'
import { useWorkspace } from '../context/workspace'
import { Filter, PageHeading, Panel, SearchBox, State } from '../components/Common'
import { OrganizationTable } from '../components/Tables'
export default function Entities() {
  const { risk, reports, refresh } = useWorkspace()
  const [query, setQuery] = useState(''), [sector, setSector] = useState(''), [level, setLevel] = useState('')
  const rows = reports.filter(r => `${r.entity_id} ${r.entity_name}`.toLowerCase().includes(query.toLowerCase()) && (!sector || r.sector === sector) && (!level || r.overall_level === level))
  return <><PageHeading title="Organizations" description="A consistent supervisory view across sectors, findings and risk components." /><State {...risk} retry={refresh}><Panel title="Organization directory" subtitle={`${reports.length} organizations in the current assessment`}><div className="toolbar"><SearchBox value={query} onChange={setQuery} placeholder="Search organization or ID…" label="Search organizations" /><Filter label="Sector" value={sector} onChange={setSector} options={[...new Set(reports.map(r => r.sector).filter(Boolean))]} /><Filter label="Risk level" value={level} onChange={setLevel} options={['LOW', 'MODERATE', 'HIGH', 'CRITICAL']} /></div><OrganizationTable reports={rows} /></Panel></State></>
}
