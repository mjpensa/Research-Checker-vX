'use client'

import { useState } from 'react'
import { FileUpload } from '@/components/features/pipeline/FileUpload'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { apiClient } from '@/lib/api-client'
import { Pipeline } from '@/types'

export default function DashboardPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null)

  const handleCreatePipeline = async () => {
    setLoading(true)
    try {
      const response = await apiClient.createPipeline({
        name: `Pipeline ${new Date().toLocaleDateString()}`,
        metadata: { created_from: 'dashboard' }
      })
      setSelectedPipeline(response.data.id)
      alert('Pipeline created! ID: ' + response.data.id)
    } catch (error) {
      console.error('Failed to create pipeline:', error)
      alert('Failed to create pipeline')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (files: File[]) => {
    if (!selectedPipeline) {
      alert('Please create a pipeline first')
      return
    }

    setLoading(true)
    try {
      await apiClient.uploadDocuments(selectedPipeline, files, 'gpt-4')
      alert(`Uploaded ${files.length} files successfully!`)

      // Start the pipeline
      await apiClient.startPipeline(selectedPipeline)
      alert('Pipeline started! Check the backend for progress.')
    } catch (error) {
      console.error('Failed to upload files:', error)
      alert('Failed to upload files')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Research Checker
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Cross-LLM Research Synthesis System
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Create Pipeline</CardTitle>
              <CardDescription>
                Start a new research analysis pipeline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleCreatePipeline}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <Spinner size="sm" />
                    Creating...
                  </div>
                ) : (
                  'Create New Pipeline'
                )}
              </Button>
              {selectedPipeline && (
                <div className="mt-4 p-3 bg-blue-50 rounded-md">
                  <p className="text-sm font-medium text-blue-900">
                    Active Pipeline
                  </p>
                  <p className="text-xs text-blue-700 font-mono mt-1">
                    {selectedPipeline}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Upload Documents</CardTitle>
              <CardDescription>
                Upload research documents for analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload
                onUpload={handleFileUpload}
                disabled={!selectedPipeline || loading}
                maxFiles={5}
              />
              {!selectedPipeline && (
                <p className="text-xs text-gray-500 mt-2">
                  Create a pipeline first before uploading documents
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Phase 4 Progress</CardTitle>
            <CardDescription>
              Frontend Foundation Complete
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="success">✓</Badge>
                <span className="text-sm">Next.js 14 Setup</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">✓</Badge>
                <span className="text-sm">TypeScript & Tailwind CSS</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">✓</Badge>
                <span className="text-sm">API Client & WebSocket Hook</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">✓</Badge>
                <span className="text-sm">UI Components (Button, Card, Badge, Spinner)</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">✓</Badge>
                <span className="text-sm">File Upload Component</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="warning">⏳</Badge>
                <span className="text-sm">Claims Table (Pending)</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="warning">⏳</Badge>
                <span className="text-sm">Dependency Graph Visualization (Pending)</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="warning">⏳</Badge>
                <span className="text-sm">Report Viewer (Pending)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
