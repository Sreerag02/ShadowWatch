import { useState } from 'react'
import { segment } from '../api/client'
import { useApi } from '../hooks/useApi'
import { useWorkspace } from '../context/workspace'
import { Empty, Facts, Panel, State } from './Common'
import { number, time } from '../utils/format'
export default function Telemetry({ finding }) {
  const { revision, refresh } = useWorkspace()
  const request = useApi(`/assets/${segment(finding.asset_id)}/telemetry?entity_id=${segment(finding.entity_id)}`, { revision, pageSize: 5000 })
  const [selected, setSelected] = useState(null)
  const evidence = finding.evidence || {}
  const all = request.data || []
  const points = all.filter(r => r.event_count != null && Number.isFinite(r.event_count) && Number.isFinite(Date.parse(r.timestamp)))
  const start = Math.min(...points.map(r => Date.parse(r.timestamp))), end = Math.max(...points.map(r => Date.parse(r.timestamp)))
  const ymax = Math.max(1, evidence.baseline_activity || 0, ...points.map(r => r.event_count))
  const x = value => 60 + (Date.parse(value) - start) / (end - start || 1) * 840
  const y = value => 210 - value / ymax * 175
  const displayed = points.find(p => p.telemetry_id === selected)
  return <Panel title="Monitoring visibility" subtitle="Actual telemetry observations · Event count per recorded interval"><Facts items={[["Asset", finding.asset_id], ["Historical baseline", evidence.baseline_activity == null ? null : `${number(evidence.baseline_activity, 1)} events`], ["Observed activity", evidence.observed_activity == null ? null : `${number(evidence.observed_activity, 1)} events`], ["Drop", evidence.drop_percentage == null ? null : `${number(evidence.drop_percentage, 1)}%`], ["Episode start", time(evidence.start_time)], ["Episode end", time(evidence.end_time)]]} />
    <State {...request} retry={refresh}>{points.length ? <div className="telemetry-chart"><svg viewBox="0 0 940 260" role="group" aria-label="Recorded asset telemetry, with the backend historical baseline"><title>Actual event counts and historical episode baseline</title>
      {[0, .5, 1].map(t => <g key={t}><line x1="60" x2="900" y1={y(ymax * t)} y2={y(ymax * t)} stroke="var(--border)" /><text x="48" y={y(ymax * t) + 4} textAnchor="end">{number(ymax * t)}</text></g>)}
      {evidence.start_time && evidence.end_time && <rect x={Math.max(60, x(evidence.start_time))} y="30" width={Math.max(2, Math.min(900, x(evidence.end_time)) - Math.max(60, x(evidence.start_time)))} height="180" fill="var(--medium)" opacity=".10" />}
      {evidence.start_time && evidence.end_time && <text x={Math.max(60, Math.min(820, x(evidence.start_time)))} y="20">Blind spot</text>}
      {evidence.baseline_activity != null && <line x1="60" x2="900" y1={y(evidence.baseline_activity)} y2={y(evidence.baseline_activity)} stroke="var(--medium)" strokeDasharray="5 5" />}
      {points.map(p => <g key={p.telemetry_id}><line x1={x(p.timestamp)} x2={x(p.timestamp)} y1={y(0)} y2={y(p.event_count)} stroke="var(--accent)" strokeWidth="1" opacity=".7" /><circle cx={x(p.timestamp)} cy={y(p.event_count)} r="3" fill="var(--accent-hover)" tabIndex={0} role="button" aria-label={`${time(p.timestamp)}: ${p.event_count} events`} onFocus={() => setSelected(p.telemetry_id)} onMouseEnter={() => setSelected(p.telemetry_id)} onClick={() => setSelected(p.telemetry_id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected(p.telemetry_id) } }}><title>{time(p.timestamp)}: {p.event_count} events</title></circle></g>)}
      <text x="60" y="240">{time(points[0].timestamp)}</text><text x="900" y="240" textAnchor="end">{time(points[points.length - 1].timestamp)}</text>
    </svg><div className="chart-legend"><span><i className="legend-blue" />Recorded events</span><span><i className="legend-gold" />Historical episode baseline</span><span>Shaded area: detected episode</span></div><p className="chart-readout" aria-live="polite">{displayed ? `${time(displayed.timestamp)} · ${number(displayed.event_count)} events · ${displayed.telemetry_id}` : 'Hover or focus an observation to inspect its value.'}</p><p className="chart-footnote">{all.length} records loaded; {all.length - points.length} without a plottable count/timestamp. No missing observations or recovery points are invented. Timestamps shown as recorded.</p></div> : <Empty title="No plottable telemetry" description="The API supplied no valid event-count observations for this asset." />}</State>
  </Panel>
}
