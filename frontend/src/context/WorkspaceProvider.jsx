import { useMemo, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { WorkspaceContext } from './workspace'

export default function WorkspaceProvider({ children }) {
  const [revision, setRevision] = useState(0)
  const risk = useApi('/risk/entities', { revision })
  const entities = useApi('/entities', { revision })
  const health = useApi('/health', { revision })
  const reports = useMemo(() => risk.data || [], [risk.data])
  const findings = useMemo(() => reports.flatMap(r => r.findings), [reports])
  const priorities = useMemo(() => reports.flatMap(r => r.priority_cases).sort((a, b) => b.priority_score - a.priority_score || a.entity_id.localeCompare(b.entity_id) || a.case_id.localeCompare(b.case_id)), [reports])
  const value = { risk, entities, health, reports, findings, priorities, revision, refresh: () => setRevision(v => v + 1),
    entityName: id => (entities.data || reports).find(r => r.entity_id === id)?.entity_name || id }
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}
