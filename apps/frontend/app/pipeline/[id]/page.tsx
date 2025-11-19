'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { ClaimsTable } from '@/components/features/claims/ClaimsTable'
import { DependencyGraph } from '@/components/features/dependencies/DependencyGraph'
import { ReportViewer, ReportList } from '@/components/features/reports/ReportViewer'
import { apiClient } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Pipeline, Claim, Dependency, Report } from '@/types'
import { formatDate } from '@/lib/utils'
import {
  FileText,
  Network,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  ArrowLeft,
} from 'lucide-react'
import Link from 'next/link'

export default function PipelineDetailPage() {
  const params = useParams()
  const pipelineId = params.id as string

  const [pipeline, setPipeline] = useState<Pipeline | null>(null)
  const [claims, setClaims] = useState<Claim[]>([])
  const [dependencies, setDependencies] = useState<Dependency[]>([])
  const [reports, setReports] = useState<Report[]>([])
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'claims' | 'graph' | 'reports'>('overview')

  const { messages, connected } = useWebSocket(pipelineId)

  // Fetch pipeline data
  useEffect(() => {
    if (!pipelineId) return

    const fetchData = async () => {
      try {
        setLoading(true)
        const [pipelineRes, claimsRes, reportsRes] = await Promise.all([
          apiClient.getPipeline(pipelineId),
          apiClient.getClaims({ pipeline_id: pipelineId, limit: 100 }),
          apiClient.getReports(pipelineId),
        ])

        setPipeline(pipelineRes.data)
        setClaims(claimsRes.data?.claims || claimsRes.data || [])
        setReports(reportsRes.data || [])

        // Fetch dependencies if available
        if (pipelineRes.data.total_dependencies > 0) {
          // Note: We don't have a getDependencies endpoint in the current API client
          // This would need to be implemented
        }
      } catch (error) {
        console.error('Failed to fetch pipeline data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [pipelineId])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'destructive' | 'secondary'> = {
      completed: 'success',
      processing: 'warning',
      failed: 'destructive',
      pending: 'secondary',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  const handleAnalyzeDependencies = async () => {
    try {
      await apiClient.analyzeDependencies(pipelineId)
      alert('Dependency analysis started! Check back in a few moments.')
    } catch (error) {
      console.error('Failed to start dependency analysis:', error)
      alert('Failed to start dependency analysis')
    }
  }

  const handleDetectContradictions = async () => {
    try {
      await apiClient.detectContradictions(pipelineId)
      alert('Contradiction detection started!')
    } catch (error) {
      console.error('Failed to detect contradictions:', error)
      alert('Failed to detect contradictions')
    }
  }

  const handleGenerateReport = async () => {
    try {
      await apiClient.generateReport(pipelineId, 'synthesis')
      alert('Report generation started!')
      // Refresh reports after a delay
      setTimeout(async () => {
        const reportsRes = await apiClient.getReports(pipelineId)
        setReports(reportsRes.data || [])
      }, 5000)
    } catch (error) {
      console.error('Failed to generate report:', error)
      alert('Failed to generate report')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!pipeline) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="py-12 text-center">
            <p className="text-gray-600">Pipeline not found</p>
            <Link href="/dashboard">
              <Button className="mt-4">Back to Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">
                {pipeline.name || `Pipeline ${pipelineId.substring(0, 8)}`}
              </h1>
              <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                Created {formatDate(pipeline.created_at)}
                {connected && (
                  <Badge variant="success" className="text-xs">
                    Live
                  </Badge>
                )}
              </p>
            </div>
            {getStatusBadge(pipeline.status)}
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b">
            {['overview', 'claims', 'graph', 'reports'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid gap-6 md:grid-cols-3">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardDescription>Total Claims</CardDescription>
                    <FileText className="h-5 w-5 text-blue-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-gray-900">
                    {pipeline.total_claims}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardDescription>Dependencies</CardDescription>
                    <Network className="h-5 w-5 text-green-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-gray-900">
                    {pipeline.total_dependencies}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardDescription>Contradictions</CardDescription>
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-gray-900">
                    {pipeline.total_contradictions}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Analysis Actions</CardTitle>
                <CardDescription>
                  Run analysis tasks on your pipeline
                </CardDescription>
              </CardHeader>
              <CardContent className="flex gap-3">
                <Button onClick={handleAnalyzeDependencies}>
                  <Network className="h-4 w-4 mr-2" />
                  Analyze Dependencies
                </Button>
                <Button onClick={handleDetectContradictions} variant="outline">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Detect Contradictions
                </Button>
                <Button onClick={handleGenerateReport} variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Report
                </Button>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            {messages.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {messages.slice(-10).reverse().map((msg, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        <span className="text-blue-600">•</span>
                        <div className="flex-1">
                          <p className="font-medium">{msg.type.replace(/_/g, ' ')}</p>
                          <p className="text-gray-500 text-xs">{formatDate(msg.timestamp)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Claims Tab */}
        {activeTab === 'claims' && (
          <ClaimsTable claims={claims} onClaimSelect={(claim) => console.log(claim)} />
        )}

        {/* Graph Tab */}
        {activeTab === 'graph' && (
          <DependencyGraph
            claims={claims}
            dependencies={dependencies}
            onNodeClick={(node) => console.log(node)}
          />
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-6">
            {selectedReport ? (
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedReport(null)}
                  className="mb-4"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Reports
                </Button>
                <ReportViewer report={selectedReport} />
              </div>
            ) : (
              <ReportList
                reports={reports}
                onSelectReport={setSelectedReport}
              />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
