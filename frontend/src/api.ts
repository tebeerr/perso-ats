import type { Analysis, HistoryItem } from './types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options)
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail?.message ?? 'Something went wrong. Please try again.')
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

export async function uploadResume(file: File) {
  const form = new FormData(); form.append('file', file)
  return request<{resume_id: number; filename: string}>('/api/resumes/upload', { method: 'POST', body: form })
}
export const createAnalysis = (resume_id: number, job_description: string) => request<Analysis>('/api/analyses', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({resume_id, job_description}) })
export const getHistory = () => request<HistoryItem[]>('/api/analyses')
export const getAnalysis = (id: number) => request<Analysis>(`/api/analyses/${id}`)
export const deleteAnalysis = (id: number) => request<void>(`/api/analyses/${id}`, {method: 'DELETE'})
export const reportUrl = (id: number) => `/api/analyses/${id}/report`

