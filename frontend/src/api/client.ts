import type { Project } from '../types/project'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly errors: string[],
    public readonly warnings: string[] = [],
  ) {
    super(errors.join('\n'))
    this.name = 'ApiError'
  }
}

async function extractErrors(res: Response): Promise<{ errors: string[]; warnings: string[] }> {
  let body: unknown
  try {
    body = await res.json()
  } catch {
    return { errors: [`HTTP ${res.status}: ${res.statusText}`], warnings: [] }
  }

  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as Record<string, unknown>).detail

    // Our custom error format: { errors: string[], warnings: string[] }
    if (detail && typeof detail === 'object' && !Array.isArray(detail) && 'errors' in detail) {
      const d = detail as { errors: unknown; warnings?: unknown }
      const errors = Array.isArray(d.errors) ? (d.errors as string[]) : [String(d.errors)]
      const warnings = Array.isArray(d.warnings) ? (d.warnings as string[]) : []
      return { errors, warnings }
    }

    // Pydantic validation error format: array of { loc, msg, type }
    if (Array.isArray(detail)) {
      const errors = detail.map((e: unknown) => {
        if (e && typeof e === 'object' && 'msg' in e) {
          const item = e as { loc?: unknown[]; msg?: string }
          const loc = Array.isArray(item.loc) ? item.loc.join('.') : ''
          return loc ? `${loc}: ${item.msg ?? ''}` : (item.msg ?? JSON.stringify(e))
        }
        return String(e)
      })
      return { errors, warnings: [] }
    }

    return { errors: [String(detail)], warnings: [] }
  }

  return { errors: [`HTTP ${res.status}: ${res.statusText}`], warnings: [] }
}

export async function postPreview(project: Project): Promise<Blob> {
  const res = await fetch('/api/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!res.ok) {
    const { errors, warnings } = await extractErrors(res)
    throw new ApiError(res.status, errors, warnings)
  }
  return res.blob()
}

export async function postValidate(
  project: Project,
): Promise<{ valid: boolean; errors: string[]; warnings: string[] }> {
  const res = await fetch('/api/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!res.ok) {
    const { errors, warnings } = await extractErrors(res)
    throw new ApiError(res.status, errors, warnings)
  }
  return res.json() as Promise<{ valid: boolean; errors: string[]; warnings: string[] }>
}

export async function postExport(project: Project, fmt: 'step' | 'stl' | '3mf'): Promise<Blob> {
  const res = await fetch(`/api/export/${fmt}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  if (!res.ok) {
    const { errors, warnings } = await extractErrors(res)
    throw new ApiError(res.status, errors, warnings)
  }
  return res.blob()
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch('/api/health')
    return res.ok
  } catch {
    return false
  }
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
