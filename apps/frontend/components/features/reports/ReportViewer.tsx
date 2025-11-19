'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, FileText, Calendar } from 'lucide-react'
import { Report } from '@/types'
import { formatDate } from '@/lib/utils'

interface ReportViewerProps {
  report: Report
  onDownload?: (format: 'pdf' | 'docx' | 'html') => void
}

export function ReportViewer({ report, onDownload }: ReportViewerProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-5 w-5 text-gray-500" />
              <CardTitle>{report.title}</CardTitle>
              <Badge variant="secondary">{report.report_type}</Badge>
            </div>
            <CardDescription className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(report.generated_at)}
              </span>
            </CardDescription>
          </div>

          {onDownload && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload('pdf')}
              >
                <Download className="h-4 w-4 mr-2" />
                PDF
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload('docx')}
              >
                <Download className="h-4 w-4 mr-2" />
                DOCX
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload('html')}
              >
                <Download className="h-4 w-4 mr-2" />
                HTML
              </Button>
            </div>
          )}
        </div>

        {report.summary && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm font-medium text-blue-900 mb-1">Executive Summary</p>
            <p className="text-sm text-blue-800">{report.summary}</p>
          </div>
        )}
      </CardHeader>

      <CardContent>
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  )
}

interface ReportListProps {
  reports: Report[]
  onSelectReport: (report: Report) => void
}

export function ReportList({ reports, onSelectReport }: ReportListProps) {
  if (reports.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No reports generated yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Complete the analysis pipeline to generate reports
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {reports.map((report) => (
        <Card
          key={report.id}
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onSelectReport(report)}
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="h-4 w-4 text-gray-500" />
                  <CardTitle className="text-lg">{report.title}</CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {report.report_type}
                  </Badge>
                </div>
                <CardDescription className="text-sm">
                  Generated {formatDate(report.generated_at)}
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm">
                View →
              </Button>
            </div>
          </CardHeader>

          {report.summary && (
            <CardContent>
              <p className="text-sm text-gray-600 line-clamp-3">{report.summary}</p>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  )
}
