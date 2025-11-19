"""
Dependency Inference Worker
Analyzes relationships between claims and builds dependency graph
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Tuple
from uuid import UUID, uuid4
import json

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../packages/database'))

from base_worker import BaseWorker
from config import config
from models import Dependency, Claim, Pipeline, DependencyType
import google.generativeai as genai
from sqlalchemy import select, func
from datetime import datetime
import networkx as nx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dependency analysis prompt
DEPENDENCY_PROMPT = """Analyze the semantic relationship between these two research claims:

Claim A (ID: {claim_a_id}):
Text: "{claim_a_text}"
Type: {claim_a_type}

Claim B (ID: {claim_b_id}):
Text: "{claim_b_text}"
Type: {claim_b_type}

Determine the PRIMARY relationship type:
- CAUSAL: A causes or enables B (or vice versa)
- EVIDENTIAL: A provides evidence supporting B (or vice versa)
- TEMPORAL: A precedes B chronologically
- PREREQUISITE: B requires A to be true
- CONTRADICTORY: A and B are mutually exclusive
- REFINES: B is a more specific version of A
- NONE: No significant relationship

Return ONLY valid JSON:
{{
  "relationship_type": "EVIDENTIAL",
  "direction": "A_to_B",
  "confidence": 0.85,
  "explanation": "Clear reasoning here",
  "semantic_markers": ["keyword1", "keyword2"],
  "strength": "moderate"
}}

Direction options: A_to_B, B_to_A, or bidirectional
Strength options: weak, moderate, strong
"""

class DependencyInferenceWorker(BaseWorker):
    """Worker for inferring dependencies between claims"""

    def __init__(self):
        super().__init__("dependency-inference-worker")

        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def generate_smart_pairs(self, claims: List[Dict], max_pairs: int = 300) -> List[Tuple[Dict, Dict]]:
        """Generate intelligent claim pairs likely to have relationships"""

        if len(claims) < 2:
            return []

        pairs = []

        # Strategy 1: High-confidence claims with all others
        claims_sorted = sorted(claims, key=lambda x: x.get('confidence', 0), reverse=True)
        top_20_percent = max(1, len(claims) // 5)
        important_claims = claims_sorted[:top_20_percent]

        for important_claim in important_claims:
            for other_claim in claims:
                if important_claim['id'] != other_claim['id']:
                    pairs.append((important_claim, other_claim))

        # Strategy 2: Within-type pairs (same claim type often related)
        by_type = {}
        for claim in claims:
            claim_type = claim.get('type', 'unknown')
            if claim_type not in by_type:
                by_type[claim_type] = []
            by_type[claim_type].append(claim)

        for type_claims in by_type.values():
            if len(type_claims) > 1:
                for i, claim_a in enumerate(type_claims):
                    for claim_b in type_claims[i+1:min(i+4, len(type_claims))]:
                        pairs.append((claim_a, claim_b))

        # Remove duplicates
        unique_pair_ids = set()
        unique_pairs = []

        for pair in pairs:
            pair_id = tuple(sorted([pair[0]['id'], pair[1]['id']]))
            if pair_id not in unique_pair_ids:
                unique_pair_ids.add(pair_id)
                unique_pairs.append(pair)

        # Limit to max_pairs
        return unique_pairs[:max_pairs]

    async def analyze_claim_pair(self, claim_a: Dict, claim_b: Dict) -> Dict:
        """Analyze relationship between two claims using Gemini"""

        prompt = DEPENDENCY_PROMPT.format(
            claim_a_id=str(claim_a['id']),
            claim_a_text=claim_a['text'][:500],  # Limit length
            claim_a_type=claim_a.get('type', 'unknown'),
            claim_b_id=str(claim_b['id']),
            claim_b_text=claim_b['text'][:500],
            claim_b_type=claim_b.get('type', 'unknown')
        )

        try:
            # Run in thread pool since genai is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.1,
                        'top_p': 0.95,
                        'max_output_tokens': 1024,
                        'response_mime_type': 'application/json'
                    }
                )
            )

            result = json.loads(response.text)

            # Add claim IDs
            result['claim_a_id'] = claim_a['id']
            result['claim_b_id'] = claim_b['id']

            return result

        except Exception as e:
            logger.error(f"Error analyzing pair: {e}")
            return None

    async def calculate_graph_metrics(self, pipeline_id: UUID):
        """Calculate graph-based metrics for claims using NetworkX"""

        logger.info(f"Calculating graph metrics for pipeline {pipeline_id}")

        async for db in self.get_db():
            try:
                # Fetch all dependencies
                result = await db.execute(
                    select(
                        Dependency.source_claim_id,
                        Dependency.target_claim_id,
                        Dependency.confidence
                    ).where(Dependency.pipeline_id == pipeline_id)
                )
                edges = result.all()

                if not edges:
                    logger.warning("No dependencies found for graph metrics")
                    return

                # Build directed graph
                G = nx.DiGraph()
                for source_id, target_id, confidence in edges:
                    G.add_edge(str(source_id), str(target_id), weight=float(confidence))

                logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

                # Calculate PageRank
                try:
                    pagerank = nx.pagerank(G, weight='weight')
                except:
                    pagerank = {}
                    logger.warning("Could not calculate PageRank")

                # Calculate betweenness centrality
                try:
                    centrality = nx.betweenness_centrality(G)
                except:
                    centrality = {}
                    logger.warning("Could not calculate centrality")

                # Identify foundational claims (many outgoing, few incoming)
                foundational_claims = set()
                for node in G.nodes():
                    in_degree = G.in_degree(node)
                    out_degree = G.out_degree(node)

                    if out_degree >= 3 and in_degree <= 2:
                        foundational_claims.add(node)

                logger.info(f"Identified {len(foundational_claims)} foundational claims")

                # Update claims with metrics
                for node in G.nodes():
                    node_uuid = UUID(node)
                    pr = pagerank.get(node, 0.0)
                    cent = centrality.get(node, 0.0)
                    is_found = node in foundational_claims

                    # Combined importance score
                    importance = pr * 0.7 + cent * 0.3

                    result = await db.execute(
                        select(Claim).where(Claim.id == node_uuid)
                    )
                    claim = result.scalar_one_or_none()

                    if claim:
                        claim.pagerank = pr
                        claim.centrality = cent
                        claim.is_foundational = is_found
                        claim.importance_score = importance

                await db.commit()
                logger.info("Graph metrics updated successfully")

            except Exception as e:
                logger.error(f"Error calculating graph metrics: {e}", exc_info=True)
                await db.rollback()

    async def process_job(self, job: Dict) -> Any:
        """Process a dependency inference job"""

        job_id = job['id']
        data = job['data']

        pipeline_id = UUID(data['pipeline_id'])
        batch_size = data.get('batch_size', 15)

        logger.info(f"Processing dependency inference for pipeline {pipeline_id}")

        async for db in self.get_db():
            try:
                # Fetch all claims for this pipeline
                result = await db.execute(
                    select(Claim).where(Claim.pipeline_id == pipeline_id)
                    .order_by(Claim.confidence.desc())
                )
                claims = result.scalars().all()

                logger.info(f"Found {len(claims)} claims to analyze")

                if len(claims) < 2:
                    logger.warning("Not enough claims for dependency analysis")
                    return {'dependencies_found': 0}

                # Convert to dict format
                claims_data = [
                    {
                        'id': claim.id,
                        'text': claim.text,
                        'type': claim.claim_type.value if claim.claim_type else 'unknown',
                        'confidence': claim.confidence or 0.8
                    }
                    for claim in claims
                ]

                # Update job status
                await self.update_job_status(job_id, 'active', progress=10)

                # Generate smart pairs
                claim_pairs = self.generate_smart_pairs(claims_data, max_pairs=250)
                logger.info(f"Generated {len(claim_pairs)} claim pairs to analyze")

                await self.update_job_status(job_id, 'active', progress=20)

                # Analyze pairs in batches
                dependencies_found = 0

                for i in range(0, len(claim_pairs), batch_size):
                    batch = claim_pairs[i:i+batch_size]

                    for claim_a, claim_b in batch:
                        dep_data = await self.analyze_claim_pair(claim_a, claim_b)

                        if not dep_data:
                            continue

                        # Only keep if relationship found (not NONE)
                        if dep_data.get('relationship_type', 'NONE').upper() == 'NONE':
                            continue

                        # Determine source and target based on direction
                        direction = dep_data.get('direction', 'A_to_B')

                        if direction == 'A_to_B':
                            source_id = dep_data['claim_a_id']
                            target_id = dep_data['claim_b_id']
                        elif direction == 'B_to_A':
                            source_id = dep_data['claim_b_id']
                            target_id = dep_data['claim_a_id']
                        else:  # bidirectional - create two edges
                            source_id = dep_data['claim_a_id']
                            target_id = dep_data['claim_b_id']

                        # Map relationship type to enum
                        rel_type_str = dep_data.get('relationship_type', 'EVIDENTIAL').upper()
                        try:
                            rel_type = DependencyType[rel_type_str]
                        except KeyError:
                            rel_type = DependencyType.EVIDENTIAL

                        # Create dependency
                        dependency = Dependency(
                            pipeline_id=pipeline_id,
                            source_claim_id=source_id,
                            target_claim_id=target_id,
                            relationship_type=rel_type,
                            confidence=dep_data.get('confidence', 0.8),
                            strength=dep_data.get('strength', 'moderate'),
                            explanation=dep_data.get('explanation', ''),
                            semantic_markers=dep_data.get('semantic_markers', [])
                        )

                        db.add(dependency)
                        dependencies_found += 1

                    # Commit batch
                    await db.commit()

                    # Update progress
                    progress = 20 + int((i / len(claim_pairs)) * 60)
                    await self.update_job_status(job_id, 'active', progress=progress)

                    logger.info(f"Processed batch {i//batch_size + 1}/{(len(claim_pairs)-1)//batch_size + 1}")

                logger.info(f"Found {dependencies_found} dependencies")

                # Update pipeline stats
                await self.update_job_status(job_id, 'active', progress=85)

                count_result = await db.execute(
                    select(func.count(Dependency.id)).where(Dependency.pipeline_id == pipeline_id)
                )
                total_deps = count_result.scalar()

                pipeline_result = await db.execute(
                    select(Pipeline).where(Pipeline.id == pipeline_id)
                )
                pipeline = pipeline_result.scalar_one_or_none()

                if pipeline:
                    pipeline.total_dependencies = total_deps
                    pipeline.updated_at = datetime.utcnow()
                    await db.commit()

                # Calculate graph metrics
                await self.update_job_status(job_id, 'active', progress=90)
                await self.calculate_graph_metrics(pipeline_id)

                return {
                    'dependencies_found': dependencies_found,
                    'total_pairs_analyzed': len(claim_pairs),
                    'pipeline_id': str(pipeline_id)
                }

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                await db.rollback()
                raise

async def main():
    """Main entry point for the worker"""

    worker = DependencyInferenceWorker()

    try:
        await worker.connect()
        await worker.run('dependency_inference')
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.stop()
    finally:
        await worker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
