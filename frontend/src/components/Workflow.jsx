import { Check, CircleHelp, Minus, X } from 'lucide-react'
import { Badge, Empty, Info, Panel } from './Common'
import { human } from '../utils/format'
export default function Workflow({ workflow }) {
  if (!workflow) return <Empty title="Workflow assessment unavailable" />
  return <Panel title="Expected vs observed" subtitle="Control matrix · Scoped workflow expectations" action={<Badge value={workflow.assessment} />}>
    {!workflow.assessment_in_scope && <Info>This alert severity is outside the HIGH/CRITICAL workflow policy. No missing-stage requirement is inferred.</Info>}
    <div className="workflow-grid"><div className="workflow-head">WORKFLOW STAGE</div><div className="workflow-head">EXPECTED</div><div className="workflow-head">OBSERVED</div>
      {Object.entries(workflow.expected || {}).map(([stage, expected]) => {
        const observed = workflow.observed?.[stage]
        const gap = expected === true && observed === false
        return <div className={`workflow-stage ${gap ? 'gap' : ''}`} key={stage}><strong>{human(stage)}</strong><span>{expected === true ? <><Check size={15} />Required</> : <><Minus size={15} />No policy</>}</span><span className={observed === true ? 'good-text' : gap ? 'danger-text' : 'muted'}>{observed === true ? <><Check size={15} />Present</> : observed === false ? <><X size={15} />Absent</> : <><CircleHelp size={15} />Unknown / mixed</>}</span></div>
      })}</div>
    <div className="workflow-summary"><strong>Auditor explanation</strong><p className="preserve-lines">{workflow.explanation}</p></div>
    <details className="disclosure"><summary>Policy limits and unresolved evidence</summary><ul>{(workflow.limitations || []).map((text, i) => <li key={i}>{text}</li>)}</ul>{workflow.data_issues?.length > 0 && <ul>{workflow.data_issues.map((item, i) => <li key={i}>{item.stage}: {item.reason}</li>)}</ul>}</details>
  </Panel>
}
