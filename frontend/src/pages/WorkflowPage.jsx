import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { useApi } from '../hooks/useApi'
import { segment } from '../api/client'
import { Filter, PageHeading, State, TextLink } from '../components/Common'
import Workflow from '../components/Workflow'
export default function WorkflowPage() {
  const { risk, priorities, revision, refresh } = useWorkspace()
  const [choice, setChoice] = useState('')
  const selected = choice || priorities[0]?.case_id || ''
  const request = useApi(selected ? `/cases/${segment(selected)}` : null, { revision })
  return <><PageHeading title="Expected vs observed" description="Recorded case stages against scoped workflow expectations." /><State {...risk} retry={refresh}><div className="toolbar stand-alone"><Filter label="Case assessment" value={selected} onChange={setChoice} options={priorities.map(c => ({ value: c.case_id, label: `${c.case_id} · ${c.priority_level}` }))} all="Select a case" />{selected && <TextLink to={`/cases/${selected}`}>Full case investigation</TextLink>}<Link className="text-link" to="/priority-cases">Browse priority queue →</Link></div><State {...request} retry={refresh}><Workflow workflow={request.data?.workflow} /></State></State></>
}
