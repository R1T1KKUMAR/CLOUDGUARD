export interface Finding {
  service: Service
  resource_id: string
  check_id: string
  title: string
  evidence: Record<string, unknown>
  severity: number | null
  ai_risk: string | null
  ai_recommendation: string | null
  remediation_status: RemediationStatus
  scanned_at: string
  finding_id: string
  FindingId: string
}

export type Service = 'IAM' | 'S3' | 'EC2' | 'Lambda' | 'SecurityGroup' | 'Config'

export type RemediationStatus =
  | 'OPEN'
  | 'APPROVED'
  | 'REJECTED'
  | 'REMEDIATED'
  | 'FAILED'

export interface ScanResponse {
  count: number
  findings: Finding[]
}
