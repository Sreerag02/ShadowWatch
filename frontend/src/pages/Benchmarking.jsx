import { useSearchParams } from 'react-router-dom'
import { useWorkspace } from '../context/workspace'
import { Empty, Filter, PageHeading, State } from '../components/Common'
import Benchmark from '../components/Benchmark'
export default function Benchmarking() {
  const { risk, reports, refresh } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const selected = params.get('entity') || reports[0]?.entity_id || ''
  const report = reports.find(r => r.entity_id === selected)
  return <><PageHeading title="Peer benchmarking" description="Organization metrics against valid sector peers." /><State {...risk} retry={refresh}><div className="toolbar stand-alone"><Filter label="Selected organization" value={selected} onChange={value => setParams(value ? { entity: value } : {})} options={reports.map(r => ({ value: r.entity_id, label: r.entity_name }))} all="Choose an organization" /><span className="muted">Peer groups and comparisons are provided by the backend.</span></div>{report ? <Benchmark report={report} /> : <Empty title="Select an organization" />}</State></>
}
