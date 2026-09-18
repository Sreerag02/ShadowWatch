import { useEffect, useState } from 'react'
import { get, getAll } from '../api/client'

export function useApi(path, { revision = 0, pageSize = null } = {}) {
  const key = `${path}:${revision}:${pageSize}`
  const [result, setResult] = useState({ key: null, data: null, error: null, fetchedAt: null })
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    const request = pageSize ? getAll(path, controller.signal, pageSize) : get(path, controller.signal)
    request.then(data => {
      if (!controller.signal.aborted) setResult({ key, data, error: null, fetchedAt: new Date() })
    }).catch(error => {
      if (!controller.signal.aborted) setResult({ key, data: null, error: error.message, fetchedAt: null })
    })
    return () => controller.abort()
  }, [key, path, pageSize])
  return result.key === key ? { data: result.data, error: result.error, fetchedAt: result.fetchedAt, loading: false } : { data: null, error: null, fetchedAt: null, loading: Boolean(path) }
}
