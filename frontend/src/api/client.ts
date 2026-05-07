import type { Project, ValidationResult } from '../types/project'

const BASE = import.meta.env.VITE_API_URL ?? ''

export async function apiHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/api/health`)
    return r.ok
  } catch {
    return false
  }
}

export async function apiValidate(project: Project): Promise<ValidationResult> {
  const r = await fetch(`${BASE}/api/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}))
    throw new Error(detail?.detail ?? `Validate failed: ${r.status}`)
  }
  return r.json()
}

export async function apiPreview(project: Project): Promise<Blob> {
  const r = await fetch(`${BASE}/api/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}))
    const msgs: string[] = detail?.detail?.errors ?? [detail?.detail ?? `Preview failed: ${r.status}`]
    throw new Error(msgs.join('; '))
  }
  return r.blob()
}

export async function apiExport(project: Project, fmt: 'step' | 'stl' | '3mf'): Promise<Blob> {
  const r = await fetch(`${BASE}/api/export/${fmt}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}))
    throw new Error(detail?.detail ?? `Export failed: ${r.status}`)
  }
  return r.blob()
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
