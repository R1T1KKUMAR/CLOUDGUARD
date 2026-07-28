import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Shield, User, Server, Activity, CheckCircle, XCircle, ExternalLink } from 'lucide-react'
import { getFinding, approveFinding, rejectFinding } from '../api'
import type { Finding, Service } from '../types'

const serviceIcons: Record<Service, typeof Shield> = {
  IAM: User, S3: Server, EC2: Server, Lambda: Activity,
  SecurityGroup: Shield, Config: Activity,
}

export default function FindingDetail() {
  const { id } = useParams<{ id: string }>()
  const [finding, setFinding] = useState<Finding | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getFinding(id).then(f => {
      setFinding(f)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  const handleApprove = async () => {
    if (!id) return
    setActionLoading('approve')
    try {
      const res = await approveFinding(id)
      setFinding(prev => prev ? { ...prev, remediation_status: res.status as Finding['remediation_status'] } : prev)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async () => {
    if (!id) return
    setActionLoading('reject')
    try {
      await rejectFinding(id)
      setFinding(prev => prev ? { ...prev, remediation_status: 'REJECTED' } : prev)
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    )
  }

  if (!finding) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Finding not found.</p>
        <Link to="/findings" className="text-emerald-600 hover:underline text-sm mt-2 inline-block">Back to findings</Link>
      </div>
    )
  }

  const severityLevel = finding.severity !== null
    ? finding.severity >= 90 ? 'Critical'
      : finding.severity >= 70 ? 'High'
      : finding.severity >= 50 ? 'Medium'
      : 'Low'
    : 'Unknown'

  const severityColor = finding.severity !== null
    ? finding.severity >= 90 ? 'text-red-600 bg-red-50 border-red-200'
      : finding.severity >= 70 ? 'text-orange-600 bg-orange-50 border-orange-200'
      : finding.severity >= 50 ? 'text-yellow-600 bg-yellow-50 border-yellow-200'
      : 'text-blue-600 bg-blue-50 border-blue-200'
    : 'text-gray-600 bg-gray-50 border-gray-200'

  const Icon = serviceIcons[finding.service as Service] || Shield

  const statusActions = finding.remediation_status === 'OPEN' || finding.remediation_status === 'FAILED'

  return (
    <div className="p-6 max-w-4xl space-y-6">
      <Link to="/findings" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Findings
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Icon className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-medium text-gray-500">{finding.service}</span>
              <span className="text-gray-300">/</span>
              <span className="text-sm text-gray-500">{finding.check_id}</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">{finding.title}</h1>
            <p className="text-sm font-mono text-gray-500">{finding.resource_id}</p>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${severityColor}`}>
              <span className="text-2xl font-bold">{finding.severity ?? '?'}</span>
              <div>
                <p className="text-xs font-semibold leading-tight">{severityLevel}</p>
                <p className="text-[10px] opacity-75">severity</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            finding.remediation_status === 'OPEN' ? 'bg-yellow-100 text-yellow-800' :
            finding.remediation_status === 'REMEDIATED' ? 'bg-emerald-100 text-emerald-800' :
            finding.remediation_status === 'APPROVED' ? 'bg-blue-100 text-blue-800' :
            finding.remediation_status === 'FAILED' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-600'
          }`}>
            {finding.remediation_status}
          </span>
          <span className="text-xs text-gray-400">
            Scanned {new Date(finding.scanned_at).toLocaleString()}
          </span>
        </div>
      </div>

      {finding.ai_risk && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-600" />
            AI Risk Analysis
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed">{finding.ai_risk}</p>
        </div>
      )}

      {finding.ai_recommendation && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <ExternalLink className="w-4 h-4 text-emerald-600" />
            AI Recommended Fix
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed">{finding.ai_recommendation}</p>
        </div>
      )}

      {Object.keys(finding.evidence).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Evidence</h2>
          <pre className="text-xs bg-gray-50 rounded-lg p-4 overflow-x-auto text-gray-700">
            {JSON.stringify(finding.evidence, null, 2)}
          </pre>
        </div>
      )}

      {statusActions && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Actions</h2>
          <div className="flex items-center gap-3">
            <button
              onClick={handleApprove}
              disabled={actionLoading !== null}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              <CheckCircle className="w-4 h-4" />
              {actionLoading === 'approve' ? 'Applying...' : 'Approve & Remediate'}
            </button>
            <button
              onClick={handleReject}
              disabled={actionLoading !== null}
              className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              <XCircle className="w-4 h-4" />
              {actionLoading === 'reject' ? 'Rejecting...' : 'Reject'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
