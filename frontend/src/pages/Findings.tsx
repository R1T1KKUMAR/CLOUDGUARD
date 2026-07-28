import { useState, useEffect } from 'react'
import { Shield, User, Server, Activity, Search } from 'lucide-react'
import { listFindings } from '../api'
import type { Finding, Service } from '../types'

const serviceIcons: Record<Service, typeof Shield> = {
  IAM: User, S3: Server, EC2: Server, Lambda: Activity,
  SecurityGroup: Shield, Config: Activity,
}

const severityColor = (s: number | null) => {
  if (s === null) return 'bg-gray-400'
  if (s >= 90) return 'bg-red-600'
  if (s >= 70) return 'bg-orange-500'
  if (s >= 50) return 'bg-yellow-500'
  return 'bg-blue-500'
}

const statusColor: Record<string, string> = {
  OPEN: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  REJECTED: 'bg-gray-100 text-gray-600',
  REMEDIATED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-red-100 text-red-800',
}

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [search, setSearch] = useState('')
  const [filterService, setFilterService] = useState<string>('all')

  useEffect(() => {
    listFindings().then(setFindings).catch(() => {})
  }, [])

  const filtered = findings.filter(f => {
    const matchesSearch = search === '' ||
      f.title.toLowerCase().includes(search.toLowerCase()) ||
      f.resource_id.toLowerCase().includes(search.toLowerCase()) ||
      f.finding_id.toLowerCase().includes(search.toLowerCase())
    const matchesService = filterService === 'all' || f.service === filterService
    return matchesSearch && matchesService
  })

  const services = [...new Set(findings.map(f => f.service))]

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Findings</h1>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search findings..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <select
          value={filterService}
          onChange={e => setFilterService(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="all">All Services</option>
          {services.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Severity</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Service</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Finding</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Resource</th>
                <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-5 py-3 font-medium text-gray-600">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map(f => {
                const Icon = serviceIcons[f.service] || Shield
                return (
                  <tr
                    key={f.finding_id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => window.location.href = `/findings/${f.finding_id}`}
                  >
                    <td className="px-5 py-3.5">
                      <div className={`w-2.5 h-2.5 rounded-full ${severityColor(f.severity)}`} />
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2 text-gray-700">
                        <Icon className="w-4 h-4" />
                        {f.service}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate font-medium text-gray-900">
                      {f.title}
                    </td>
                    <td className="px-5 py-3.5 text-gray-600 font-mono text-xs">
                      {f.resource_id}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusColor[f.remediation_status] || 'bg-gray-100'}`}>
                        {f.remediation_status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-medium">
                      {f.severity !== null ? f.severity : '-'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <p className="text-center py-8 text-sm text-gray-400">
            {findings.length === 0 ? 'No findings yet. Run a scan from the Dashboard.' : 'No findings match your filters.'}
          </p>
        )}
      </div>
    </div>
  )
}
