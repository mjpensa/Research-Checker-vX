"""
Report Generation Worker
Generates comprehensive synthesis reports from analyzed claims
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any
from uuid import UUID
import json

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../packages/database'))

from base_worker import BaseWorker
from config import config
from models import Report, Claim, Dependency, Contradiction, Pipeline, Document
import google.generativeai as genai
from sqlalchemy import select, func
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SYNTHESIS_REPORT_PROMPT = """Generate a comprehensive research synthesis report based on these analyzed claims:

# Claims Summary
{claims_summary}

# Dependency Graph Overview
{dependency_summary}

# Contradictions Found
{contradictions_summary}

# Statistics
- Total Claims: {total_claims}
- Total Dependencies: {total_dependencies}
- Total Contradictions: {total_contradictions}
- Foundational Claims: {foundational_claims}

Generate a professional executive synthesis report with these sections:

## 1. EXECUTIVE SUMMARY
Provide a high-level overview (2-3 paragraphs) of the key findings and insights.

## 2. CONSENSUS FINDINGS
List claims with strong evidence and multi-source agreement. Cite claim IDs like [Claim: abc-123].

## 3. KEY INSIGHTS
Identify novel connections, emergent patterns, and cross-source synthesis.

## 4. DISPUTED AREAS
Document contradictions requiring resolution, evidence gaps, and areas of uncertainty.

## 5. DEPENDENCY ANALYSIS
Analyze critical dependency chains, foundational vs derived claims, and vulnerability points.

## 6. RECOMMENDATIONS
Suggest next research steps, areas needing clarification, and priority questions.

Format the report in **Markdown**. Use clear, professional language. Be specific and cite evidence.
"""

class ReportGenerationWorker(BaseWorker):
    """Worker for generating synthesis reports"""

    def __init__(self):
        super().__init__("report-generation-worker")

        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    async def gather_report_data(self, pipeline_id: UUID) -> Dict[str, Any]:
        """Gather all data needed for report generation"""

        logger.info(f"Gathering data for pipeline {pipeline_id}")

        async for db in self.get_db():
            try:
                # Get pipeline info
                pipeline_result = await db.execute(
                    select(Pipeline).where(Pipeline.id == pipeline_id)
                )
                pipeline = pipeline_result.scalar_one_or_none()

                if not pipeline:
                    raise ValueError(f"Pipeline {pipeline_id} not found")

                # Get documents
                docs_result = await db.execute(
                    select(Document).where(Document.pipeline_id == pipeline_id)
                )
                documents = docs_result.scalars().all()

                # Get claims (top 50 by importance)
                claims_result = await db.execute(
                    select(Claim)
                    .where(Claim.pipeline_id == pipeline_id)
                    .order_by(Claim.importance_score.desc())
                    .limit(50)
                )
                claims = claims_result.scalars().all()

                # Get foundational claims
                foundational_result = await db.execute(
                    select(Claim)
                    .where(Claim.pipeline_id == pipeline_id, Claim.is_foundational == True)
                )
                foundational_claims = foundational_result.scalars().all()

                # Get dependencies
                deps_result = await db.execute(
                    select(Dependency)
                    .where(Dependency.pipeline_id == pipeline_id)
                    .order_by(Dependency.confidence.desc())
                    .limit(100)
                )
                dependencies = deps_result.scalars().all()

                # Get contradictions
                contras_result = await db.execute(
                    select(Contradiction)
                    .where(Contradiction.pipeline_id == pipeline_id)
                    .order_by(Contradiction.confidence.desc())
                )
                contradictions = contras_result.scalars().all()

                return {
                    'pipeline': pipeline,
                    'documents': documents,
                    'claims': claims,
                    'foundational_claims': foundational_claims,
                    'dependencies': dependencies,
                    'contradictions': contradictions
                }

            except Exception as e:
                logger.error(f"Error gathering data: {e}", exc_info=True)
                raise

    def format_claims_summary(self, claims: list) -> str:
        """Format claims for the report"""

        if not claims:
            return "No claims extracted."

        summary = []
        for i, claim in enumerate(claims[:20], 1):
            summary.append(
                f"{i}. [{claim.id}] {claim.text[:200]}...\n"
                f"   Type: {claim.claim_type.value if claim.claim_type else 'unknown'}, "
                f"Confidence: {claim.confidence:.2f if claim.confidence else 0}, "
                f"Importance: {claim.importance_score:.2f if claim.importance_score else 0}"
            )

        return "\n\n".join(summary)

    def format_dependency_summary(self, dependencies: list) -> str:
        """Format dependencies for the report"""

        if not dependencies:
            return "No dependencies analyzed yet."

        summary = []
        for i, dep in enumerate(dependencies[:15], 1):
            summary.append(
                f"{i}. {dep.relationship_type.value if dep.relationship_type else 'unknown'}: "
                f"[{dep.source_claim_id}] → [{dep.target_claim_id}]\n"
                f"   Confidence: {dep.confidence:.2f}, Strength: {dep.strength or 'unknown'}\n"
                f"   {dep.explanation[:150] if dep.explanation else ''}..."
            )

        return "\n\n".join(summary)

    def format_contradictions_summary(self, contradictions: list) -> str:
        """Format contradictions for the report"""

        if not contradictions:
            return "No contradictions detected."

        summary = []
        for i, contra in enumerate(contradictions[:10], 1):
            summary.append(
                f"{i}. {contra.contradiction_type or 'unknown'} ({contra.severity or 'unknown'} severity)\n"
                f"   Between: [{contra.claim_a_id}] and [{contra.claim_b_id}]\n"
                f"   Confidence: {contra.confidence:.2f if contra.confidence else 0}\n"
                f"   {contra.explanation[:150] if contra.explanation else ''}...\n"
                f"   Resolution: {contra.resolution_suggestion[:100] if contra.resolution_suggestion else 'Not provided'}..."
            )

        return "\n\n".join(summary)

    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate synthesis report using Gemini"""

        pipeline = data['pipeline']
        claims = data['claims']
        dependencies = data['dependencies']
        contradictions = data['contradictions']
        foundational_claims = data['foundational_claims']

        # Format summaries
        claims_summary = self.format_claims_summary(claims)
        dependency_summary = self.format_dependency_summary(dependencies)
        contradictions_summary = self.format_contradictions_summary(contradictions)

        prompt = SYNTHESIS_REPORT_PROMPT.format(
            claims_summary=claims_summary,
            dependency_summary=dependency_summary,
            contradictions_summary=contradictions_summary,
            total_claims=len(claims),
            total_dependencies=len(dependencies),
            total_contradictions=len(contradictions),
            foundational_claims=len(foundational_claims)
        )

        logger.info("Generating synthesis report with Gemini")

        try:
            # Run in thread pool since genai is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.2,
                        'top_p': 0.95,
                        'max_output_tokens': 8192
                    }
                )
            )

            report_content = response.text

            logger.info(f"Generated report ({len(report_content)} chars)")

            return report_content

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise

    async def process_job(self, job: Dict) -> Any:
        """Process a report generation job"""

        job_id = job['id']
        data = job['data']

        pipeline_id = UUID(data['pipeline_id'])
        report_type = data.get('report_type', 'synthesis')

        logger.info(f"Processing report generation for pipeline {pipeline_id}")

        async for db in self.get_db():
            try:
                # Update job status
                await self.update_job_status(job_id, 'active', progress=10)

                # Gather data
                report_data = await self.gather_report_data(pipeline_id)

                await self.update_job_status(job_id, 'active', progress=30)

                # Generate report
                report_content = await self.generate_report(report_data)

                await self.update_job_status(job_id, 'active', progress=70)

                # Extract key findings and recommendations
                key_findings = self.extract_key_findings(report_data)
                recommendations = self.extract_recommendations(report_data)

                # Calculate statistics
                statistics = {
                    'total_claims': len(report_data['claims']),
                    'total_dependencies': len(report_data['dependencies']),
                    'total_contradictions': len(report_data['contradictions']),
                    'foundational_claims': len(report_data['foundational_claims']),
                    'documents_analyzed': len(report_data['documents'])
                }

                # Save report to database
                report = Report(
                    pipeline_id=pipeline_id,
                    report_type=report_type,
                    title=f"{report_type.capitalize()} Report - {report_data['pipeline'].name or 'Untitled'}",
                    content=report_content,
                    summary=report_content[:500] + "...",  # First 500 chars
                    key_findings=key_findings,
                    recommendations=recommendations,
                    statistics=statistics,
                    export_formats=['markdown'],
                    export_paths={}
                )

                db.add(report)
                await db.commit()
                await db.refresh(report)

                await self.update_job_status(job_id, 'active', progress=95)

                logger.info(f"Saved report {report.id} to database")

                return {
                    'report_id': str(report.id),
                    'pipeline_id': str(pipeline_id),
                    'content_length': len(report_content)
                }

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                await db.rollback()
                raise

    def extract_key_findings(self, data: Dict) -> Dict:
        """Extract key findings from data"""

        return {
            'top_claims': [
                {'id': str(claim.id), 'text': claim.text[:100]}
                for claim in data['claims'][:5]
            ],
            'foundational_count': len(data['foundational_claims'])
        }

    def extract_recommendations(self, data: Dict) -> Dict:
        """Extract recommendations from data"""

        return {
            'areas_needing_clarification': len(data['contradictions']),
            'suggested_next_steps': [
                'Review contradictions for resolution',
                'Validate foundational claims',
                'Explore high-centrality claims further'
            ]
        }

async def main():
    """Main entry point for the worker"""

    worker = ReportGenerationWorker()

    try:
        await worker.connect()
        await worker.run('report_generation')
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.stop()
    finally:
        await worker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
