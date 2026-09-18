export const human = (value) => value ? String(value).replaceAll('_', ' ').toLowerCase().replace(/^./, c => c.toUpperCase()) : 'Not available'
export const number = (value, digits = 0) => value == null || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en', { maximumFractionDigits: digits, minimumFractionDigits: digits })
export const time = (value) => value ? String(value).replace('T', ' ').replace(/\.\d+$/, '') : 'Not recorded'
export const componentNames = { EXECUTION_GAP_RISK: 'Execution gaps', MONITORING_VISIBILITY_RISK: 'Monitoring visibility', INVESTIGATION_QUALITY_RISK: 'Investigation quality', REPEAT_INCIDENT_RISK: 'Repeat incidents', RECORD_CONSISTENCY_RISK: 'Record consistency' }
export const componentColors = ['#6b9eff', '#e6b866', '#a89af3', '#58b4b1', '#8ca2bd']
export const isHigh = (level) => ['HIGH', 'CRITICAL'].includes(level)
