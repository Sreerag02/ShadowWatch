import { useWorkspace } from '../context/workspace'
import { Badge, Facts, Info, PageHeading, Panel, State } from '../components/Common'
import { EvidenceTree } from '../components/Evidence'
export default function System() {
  const { health, risk, reports, refresh } = useWorkspace()
  return <><PageHeading title="System status" description="Connection and engine execution status from the current backend responses." action={<button className="button" onClick={refresh}>Check again</button>} /><div className="two-columns"><Panel title="Backend and database"><State {...health} retry={refresh}><Facts items={[["Backend", <Badge value={health.data?.status}>{health.data?.status || 'Unknown'}</Badge>], ["Database", <Badge value={health.data?.database}>{health.data?.database || 'Unknown'}</Badge>], ["Last checked", health.fetchedAt?.toLocaleString()]]} /></State></Panel><Panel title="Analytics execution"><State {...risk} retry={refresh}>{reports.length ? <EvidenceTree value={reports.map(r => ({ entity_id: r.entity_id, engines: r.engine_status }))} name="Organization" /> : <p className="inset">No organization execution status is available.</p>}</State></Panel></div><Info>An engine reporting available means it executed. It does not guarantee that every source record was complete or assessable.</Info></>
}
