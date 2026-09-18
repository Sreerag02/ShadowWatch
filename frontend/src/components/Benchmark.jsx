import { useWorkspace } from '../context/workspace'
import { Badge, DataGrid, Info, Empty, Panel } from './Common'
import { human, number } from '../utils/format'
export default function Benchmark({ report }) {
  const { entityName } = useWorkspace()
  const peers = report.peer_context
  const rows = Object.entries(peers.metrics).map(([key, value]) => ({ key, ...value }))
  return <Panel title="Peer context" subtitle={`${peers.peer_group || 'No peer group'} · ${peers.sector || 'Unknown sector'}`} action={<Badge value={peers.status} />}>{peers.status === 'NO_VALID_PEERS' && <Empty title="Insufficient comparable peer data" description="No other organization with a valid matching peer group and sector is available." />}<div className="peer-context"><strong>{report.entity_name}</strong><span>Compared with: {peers.peer_entity_ids.map(entityName).join(', ') || 'No comparable peers'}</span><small>Group source: {human(peers.peer_group_source)} · Selected organization excluded from peer statistics</small></div>
    <DataGrid caption="Peer comparison metrics" rows={rows} rowKey="key" pageSize={20} columns={[
      { key: 'key', label: 'Metric', render: r => <><strong>{human(r.key)}</strong><small>{r.unit}</small></> },
      { key: 'entity_value', label: 'Entity value', render: r => number(r.entity_value, 2) },
      { key: 'peer_median', label: 'Peer median', render: r => number(r.peer_median, 2) },
      { key: 'peer_mean', label: 'Peer mean', render: r => number(r.peer_mean, 2) },
      { key: 'difference', label: 'Difference', render: r => r.difference_from_peer_median == null ? '—' : `${r.difference_from_peer_median > 0 ? '+' : ''}${number(r.difference_from_peer_median, 2)}` },
      { key: 'valid_peer_count', label: 'Valid peers' },
      { key: 'description', label: 'Context', render: r => <><span>{human(r.description)}</span>{r.status !== 'AVAILABLE' && <small>{human(r.status)}</small>}</> },
    ]} /><Info>{peers.explanation} Comparisons cover loaded records, not necessarily equal observation periods.</Info></Panel>
}
