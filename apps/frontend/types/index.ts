export type PipelineStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type ClaimType = 'factual' | 'statistical' | 'causal' | 'opinion' | 'hypothesis'

export type DependencyType = 'causal' | 'evidential' | 'temporal' | 'prerequisite' | 'contradictory' | 'refines'

export interface Document {
  id: string
  filename: string
  file_size: number
  mime_type: string
  status: string
  created_at: string
}

export interface Claim {
  id: string
  text: string
  claim_type: ClaimType
  confidence: number
  evidence_type?: string
  source_span_start?: number
  source_span_end?: number
  pagerank?: number
  centrality?: number
  is_foundational: boolean
  extracted_at: string
}

export interface Dependency {
  id: string
  source_claim_id: string
  target_claim_id: string
  relationship_type: DependencyType
  confidence: number
  strength: string
  explanation: string
  semantic_markers?: string[]
}

export interface Contradiction {
  id: string
  claim_a_id: string
  claim_b_id: string
  contradiction_type: string
  severity: string
  explanation: string
  confidence: number
  resolution_suggestion?: string
}

export interface Pipeline {
  id: string
  name?: string
  status: PipelineStatus
  total_claims: number
  total_dependencies: number
  total_contradictions: number
  created_at: string
  updated_at: string
  completed_at?: string
  documents: Document[]
}

export interface Report {
  id: string
  pipeline_id: string
  report_type: string
  title: string
  content: string
  content_html: string
  summary: string
  generated_at: string
}

export interface GraphNode {
  id: string
  label: string
  type: ClaimType
  importance: number
  isFoundational: boolean
}

export interface GraphEdge {
  source: string
  target: string
  type: DependencyType
  confidence: number
}
