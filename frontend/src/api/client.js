const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export async function get(path, signal) {
  const controller = new AbortController()
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  if (signal?.aborted) controller.abort()
  const timer = setTimeout(() => controller.abort(new Error('The API request timed out. Please retry.')), 90000)
  try {
    const response = await fetch(`${baseUrl}${path}`, { signal: controller.signal, headers: { Accept: 'application/json' } })
    const type = response.headers.get('content-type') || ''
    if (!type.includes('application/json')) throw new Error(`The API returned a non-JSON response (${response.status}). Check the API connection.`)
    const body = await response.json()
    if (!response.ok) throw new Error(typeof body.detail === 'string' ? `${body.detail} (${response.status})` : `API request failed (${response.status}).`)
    return body
  } catch (error) {
    if (signal?.aborted) throw error
    if (controller.signal.aborted) throw new Error('The API request timed out. Please retry.', { cause: error })
    if (error instanceof TypeError) throw new Error('Cannot reach the backend. Check that FastAPI is running, then retry.', { cause: error })
    throw error
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export async function getAll(path, signal, pageSize = 1000) {
  const rows = []
  for (let offset = 0; ; offset += pageSize) {
    const separator = path.includes('?') ? '&' : '?'
    const page = await get(`${path}${separator}limit=${pageSize}&offset=${offset}`, signal)
    if (!Array.isArray(page)) throw new Error('Expected a paginated API list.')
    rows.push(...page)
    if (page.length < pageSize) return rows
  }
}
export const segment = (value) => encodeURIComponent(value)
