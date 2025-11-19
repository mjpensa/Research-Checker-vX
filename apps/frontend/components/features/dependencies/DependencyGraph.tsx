'use client'

import React, { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react'
import { GraphNode, GraphLink, Claim, Dependency } from '@/types'

interface DependencyGraphProps {
  claims: Claim[]
  dependencies: Dependency[]
  height?: number
  onNodeClick?: (node: GraphNode) => void
}

export function DependencyGraph({
  claims,
  dependencies,
  height = 600,
  onNodeClick,
}: DependencyGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })

  // Transform data to graph format
  const graphData = React.useMemo(() => {
    const nodes: GraphNode[] = claims.map((claim) => ({
      id: claim.id,
      label: claim.text.substring(0, 50) + '...',
      type: claim.claim_type,
      importance: claim.pagerank || 0,
      isFoundational: claim.is_foundational,
    }))

    const links: GraphLink[] = dependencies.map((dep) => ({
      source: dep.source_claim_id,
      target: dep.target_claim_id,
      type: dep.relationship_type,
      confidence: dep.confidence,
      strength: dep.strength,
    }))

    return { nodes, links }
  }, [claims, dependencies])

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
    onNodeClick?.(node)
  }

  const getNodeColor = (node: GraphNode) => {
    if (node.isFoundational) {
      return '#ef4444' // red-500
    }

    const typeColors: Record<string, string> = {
      factual: '#3b82f6', // blue-500
      statistical: '#10b981', // green-500
      causal: '#f59e0b', // amber-500
      opinion: '#8b5cf6', // violet-500
      hypothesis: '#ec4899', // pink-500
    }

    return typeColors[node.type] || '#6b7280' // gray-500
  }

  const getLinkColor = (type: string) => {
    const typeColors: Record<string, string> = {
      causal: '#ef4444', // red-500
      evidential: '#3b82f6', // blue-500
      temporal: '#10b981', // green-500
      prerequisite: '#f59e0b', // amber-500
      contradictory: '#dc2626', // red-600
      refines: '#8b5cf6', // violet-500
    }

    return typeColors[type] || '#9ca3af' // gray-400
  }

  const getNodeSize = (node: GraphNode) => {
    const baseSize = 8
    const importanceBonus = node.importance * 15
    const foundationalBonus = node.isFoundational ? 5 : 0
    return baseSize + importanceBonus + foundationalBonus
  }

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev * 1.5, 5))
  }

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev / 1.5, 0.2))
  }

  const handleFitView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const handleDownload = () => {
    if (canvasRef.current) {
      const url = canvasRef.current.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = 'dependency-graph.png'
      link.href = url
      link.click()
    }
  }

  // Simple force-directed layout simulation
  useEffect(() => {
    if (!canvasRef.current || graphData.nodes.length === 0) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height

    // Initialize node positions
    const nodePositions = new Map<string, { x: number; y: number }>()
    graphData.nodes.forEach((node, i) => {
      const angle = (i / graphData.nodes.length) * Math.PI * 2
      const radius = Math.min(width, height) * 0.3
      nodePositions.set(node.id, {
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
      })
    })

    // Draw function
    const draw = () => {
      ctx.clearRect(0, 0, width, height)
      ctx.save()
      ctx.translate(pan.x, pan.y)
      ctx.scale(zoom, zoom)

      // Draw links
      graphData.links.forEach((link) => {
        const sourcePos = nodePositions.get(link.source)
        const targetPos = nodePositions.get(link.target)
        if (!sourcePos || !targetPos) return

        ctx.beginPath()
        ctx.moveTo(sourcePos.x, sourcePos.y)
        ctx.lineTo(targetPos.x, targetPos.y)
        ctx.strokeStyle = getLinkColor(link.type)
        ctx.lineWidth = link.confidence * 2
        ctx.globalAlpha = 0.6
        ctx.stroke()
        ctx.globalAlpha = 1

        // Draw arrow
        const dx = targetPos.x - sourcePos.x
        const dy = targetPos.y - sourcePos.y
        const angle = Math.atan2(dy, dx)
        const arrowLength = 10
        ctx.beginPath()
        ctx.moveTo(
          targetPos.x - arrowLength * Math.cos(angle - Math.PI / 6),
          targetPos.y - arrowLength * Math.sin(angle - Math.PI / 6)
        )
        ctx.lineTo(targetPos.x, targetPos.y)
        ctx.lineTo(
          targetPos.x - arrowLength * Math.cos(angle + Math.PI / 6),
          targetPos.y - arrowLength * Math.sin(angle + Math.PI / 6)
        )
        ctx.fillStyle = getLinkColor(link.type)
        ctx.fill()
      })

      // Draw nodes
      graphData.nodes.forEach((node) => {
        const pos = nodePositions.get(node.id)
        if (!pos) return

        const size = getNodeSize(node)
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, size, 0, Math.PI * 2)
        ctx.fillStyle = getNodeColor(node)
        ctx.fill()

        // Draw border for selected node
        if (selectedNode?.id === node.id) {
          ctx.strokeStyle = '#1e40af' // blue-800
          ctx.lineWidth = 3
          ctx.stroke()
        }
      })

      ctx.restore()
    }

    draw()
  }, [graphData, zoom, pan, selectedNode])

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Dependency Graph</CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              {graphData.nodes.length} claims, {graphData.links.length} dependencies
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleFitView}>
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleDownload}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={800}
            height={height}
            className="w-full bg-white"
          />

          {/* Legend */}
          <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg space-y-3 text-sm">
            <div>
              <p className="font-semibold mb-2">Claim Types</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span>Factual</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Statistical</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span>Causal</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Foundational</span>
                </div>
              </div>
            </div>

            <div className="border-t pt-3">
              <p className="font-semibold mb-2">Relationships</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-blue-500" />
                  <span>Evidential</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-red-500" />
                  <span>Causal</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-0.5 bg-red-600" />
                  <span>Contradictory</span>
                </div>
              </div>
            </div>
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg max-w-md">
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <Badge variant="secondary">{selectedNode.type}</Badge>
                  {selectedNode.isFoundational && (
                    <Badge variant="destructive" className="ml-2">
                      Foundational
                    </Badge>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedNode(null)}
                >
                  ×
                </Button>
              </div>
              <p className="text-sm text-gray-900 mb-2">{selectedNode.label}</p>
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Importance:</span>{' '}
                  {(selectedNode.importance * 100).toFixed(1)}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
