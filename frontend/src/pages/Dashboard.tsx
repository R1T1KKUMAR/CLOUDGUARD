import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, AlertTriangle, Server, User, Activity, RefreshCw } from 'lucide-react'
import { triggerScan, listFindings } from '../api'
import type { Finding, Service } from '../types'

const serviceIcons: Record<Service, typeof Shield> = {
  IAM: User,
  S3: Server,
  EC2: Server,
  Lambda: Activity,
  SecurityGroup: Shield,
  Config: Activity,
}

const severityColor = (s: number | null) => {
  if (s === null) return 'bg-gray-500'
  if (s >= 90) return 'bg-red-600'
  if (s >= 70) return 'bg-orange-500'
  if (s >= 50) return 'bg-yellow-500'
  return 'bg-blue-500'
}

export default function Dashboard() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [scanning, setScanning] = useState(false)

  const load = async () => {
    try {
      setFindings(await listFindings())
    } catch { /* ignore */ }
  }

  useEffect(() => { load() }, [])

  const handleScan = async () => {
    setScanning(true)
    try {
      await triggerScan()
      await load()
    } finally {
      setScanning(false)
    }
  }

  const high = findings.filter(f => (f.severity ?? 0) >= 80).length
  const medium = findings.filter(f => {
    const s = f.severity ?? 0; return s >= 50 && s < 80
  }).length
  const low = findings.filter(f => (f.severity ?? 0) < 50).length
  const open = findings.filter(f => f.remediation_status === 'OPEN').length

  const byService: Record<string, number> = {}
  for (const f of findings) {
    byService[f.service] = (byService[f.service] ?? 0) + 1
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors text-sm font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Scanning...' : 'Run Scan'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Findings', value: findings.length, color: 'bg-blue-600', icon: AlertTriangle },
          { label: 'High Severity', value: high, color: 'bg-red-600', icon: AlertTriangle },
          { label: 'Open', value: open, color: 'bg-yellow-500', icon: AlertTriangle },
          { label: 'Resolved', value: findings.length - open, color: 'bg-emerald-600', icon: Shield },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
              </div>
              <div className={`${color} p-3 rounded-lg`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Severity Breakdown</h2>
          <div className="space-y-3">
            {[
              { label: 'Critical (80-100)', count: high, color: 'bg-red-600' },
              { label: 'Medium (50-79)', count: medium, color: 'bg-orange-500' },
              { label: 'Low (0-49)', count: low, color: 'bg-blue-500' },
            ].map(({ label, count, color }) => (
              <div key={label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{label}</span>
                  <span className="font-medium">{count}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full">
                  <div
                    className={`h-2 rounded-full ${color} transition-all`}
                    style={{ width: findings.length ? `${(count / findings.length) * 100}%` : '0%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">By Service</h2>
          <div className="space-y-3">
            {Object.entries(byService).map(([service, count]) => {
              const Icon = serviceIcons[service as Service] || Shield
              return (
                <div key={service} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700">{service}</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              )
            })}
            {findings.length === 0 && (
              <p className="text-sm text-gray-400">No findings yet. Run a scan.</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Findings</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {findings.slice(0, 5).map(f => (
            <Link
              key={f.finding_id}
              to={`/findings/${f.finding_id}`}
              className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50 transition-colors"
            >
              <div className={`w-2.5 h-2.5 rounded-full ${severityColor(f.severity)}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{f.title}</p>
                <p className="text-xs text-gray-500">{f.service} · {f.resource_id}</p>
              </div>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                f.remediation_status === 'OPEN' ? 'bg-yellow-100 text-yellow-800' :
                f.remediation_status === 'REMEDIATED' ? 'bg-emerald-100 text-emerald-800' :
                f.remediation_status === 'APPROVED' ? 'bg-blue-100 text-blue-800' :
                f.remediation_status === 'FAILED' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-600'
              }`}>
                {f.remediation_status}
              </span>
              {f.severity !== null && (
                <span className="text-sm font-mono text-gray-500 w-8 text-right">{f.severity}</span>
              )}
            </Link>
          ))}
          {findings.length === 0 && (
            <p className="px-5 py-8 text-sm text-gray-400 text-center">No findings yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
