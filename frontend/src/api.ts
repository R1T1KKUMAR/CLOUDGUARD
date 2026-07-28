const API_BASE = import.meta.env.VITE_API_URL || 'https://ei0ll3ctak.execute-api.ap-south-1.amazonaws.com'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export async function healthCheck() {
  return request<{ status: string }>('/health')
}

export async function triggerScan() {
  return request<{ count: number; findings: unknown[] }>('/scan', { method: 'POST' })
}

export async function listFindings() {
  return request<import('./types').Finding[]>('/findings')
}

export async function getFinding(id: string) {
  return request<import('./types').Finding>(`/findings/${id}`)
}

export async function approveFinding(id: string) {
  return request<{ finding_id: string; status: string }>(`/findings/${id}/approve`, { method: 'POST' })
}

export async function rejectFinding(id: string) {
  return request<{ finding_id: string; status: string }>(`/findings/${id}/reject`, { method: 'POST' })
}
