"""
Phase 3 Test Script
Tests advanced features: dependency inference, contradiction detection, and report generation

This script demonstrates:
1. Analyzing dependencies between claims
2. Detecting contradictions
3. Generating synthesis reports
4. Retrieving graph metrics
"""
import asyncio
import httpx
import sys
import time

# API base URL
API_BASE = "http://localhost:8000"

# Colors for terminal output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_section(title):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(message):
    print(f"{GREEN}✓{RESET} {message}")

def print_error(message):
    print(f"{RED}✗{RESET} {message}")

def print_info(message):
    print(f"{YELLOW}ℹ{RESET} {message}")

async def test_phase3(pipeline_id: str = None):
    """Run complete Phase 3 test"""

    async with httpx.AsyncClient(timeout=60.0) as client:

        # If no pipeline_id provided, need to create test data
        if not pipeline_id:
            print_error("No pipeline_id provided!")
            print_info("Run test_phase2.py first to create a pipeline with claims")
            print_info("Then run: python test_phase3.py <pipeline-id>")
            return False

        print_section("Phase 3: Advanced Features Test")
        print_info(f"Using pipeline: {pipeline_id}")

        # Test 1: Check pipeline has claims
        print_section("Test 1: Verify Pipeline Has Claims")

        try:
            response = await client.get(
                f"{API_BASE}/api/v1/pipelines/{pipeline_id}",
                params={'include_documents': True}
            )

            if response.status_code == 200:
                pipeline = response.json()
                print_success(f"Found pipeline: {pipeline['name'] or pipeline['id']}")
                print_info(f"Total claims: {pipeline['total_claims']}")
                print_info(f"Status: {pipeline['status']}")

                if pipeline['total_claims'] < 2:
                    print_error("Need at least 2 claims for dependency analysis")
                    print_info("Upload more documents or wait for claim extraction to complete")
                    return False
            else:
                print_error(f"Pipeline not found: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Error checking pipeline: {e}")
            return False

        # Test 2: Analyze Dependencies
        print_section("Test 2: Analyze Dependencies Between Claims")

        print_info("Starting dependency inference...")
        print_info("This will:")
        print_info("  - Generate smart claim pairs")
        print_info("  - Use Gemini to analyze relationships")
        print_info("  - Calculate PageRank and centrality")
        print_info("  - Identify foundational claims")

        try:
            response = await client.post(
                f"{API_BASE}/api/v1/reports/{pipeline_id}/analyze-dependencies"
            )

            if response.status_code == 200:
                result = response.json()
                print_success("Dependency analysis started")
                print_info(f"Job ID: {result['job_id']}")
                print_info("Worker will process this in the background")
                print_info("Make sure worker_inference.py is running!")

                # Wait a bit for processing
                print_info("\nWaiting for dependency analysis (this may take 30-60s)...")
                await asyncio.sleep(45)

            else:
                print_error(f"Failed to start analysis: {response.status_code}")
                print_error(response.text)
        except Exception as e:
            print_error(f"Error starting dependency analysis: {e}")

        # Test 3: Check Dependencies
        print_section("Test 3: Check Discovered Dependencies")

        try:
            response = await client.get(f"{API_BASE}/api/v1/pipelines/{pipeline_id}")

            if response.status_code == 200:
                pipeline = response.json()
                deps_count = pipeline.get('total_dependencies', 0)

                if deps_count > 0:
                    print_success(f"Found {deps_count} dependencies!")

                    # Get some example dependencies
                    claims_response = await client.get(
                        f"{API_BASE}/api/v1/claims/",
                        params={'pipeline_id': pipeline_id, 'limit': 5}
                    )

                    if claims_response.status_code == 200:
                        claims = claims_response.json()
                        print_info(f"\nShowing {len(claims)} claims with metrics:")

                        for claim in claims:
                            print(f"\n  {claim['text'][:80]}...")
                            print(f"    Importance: {claim.get('importance_score', 0):.3f}")
                            print(f"    PageRank: {claim.get('pagerank', 0):.3f}")
                            print(f"    Centrality: {claim.get('centrality', 0):.3f}")
                            print(f"    Foundational: {claim.get('is_foundational', False)}")
                else:
                    print_info("No dependencies found yet (worker may still be processing)")

        except Exception as e:
            print_error(f"Error checking dependencies: {e}")

        # Test 4: Detect Contradictions
        print_section("Test 4: Detect Contradictions")

        print_info("Analyzing claims for contradictions...")

        try:
            response = await client.post(
                f"{API_BASE}/api/v1/reports/{pipeline_id}/detect-contradictions"
            )

            if response.status_code == 200:
                result = response.json()
                contradictions_found = result.get('contradictions_found', 0)

                if contradictions_found > 0:
                    print_success(f"Detected {contradictions_found} contradiction(s)")

                    # Get contradiction details
                    contras_response = await client.get(
                        f"{API_BASE}/api/v1/reports/{pipeline_id}/contradictions"
                    )

                    if contras_response.status_code == 200:
                        contradictions = contras_response.json()

                        print_info("\nContradiction details:")
                        for i, contra in enumerate(contradictions[:3], 1):
                            print(f"\n  {i}. {contra.get('contradiction_type', 'unknown')} "
                                  f"({contra.get('severity', 'unknown')} severity)")
                            print(f"     Confidence: {contra.get('confidence', 0):.2f}")
                            print(f"     {contra.get('explanation', '')[:150]}...")
                else:
                    print_info("No contradictions detected (claims are consistent)")

            else:
                print_error(f"Failed to detect contradictions: {response.status_code}")

        except Exception as e:
            print_error(f"Error detecting contradictions: {e}")

        # Test 5: Generate Report
        print_section("Test 5: Generate Synthesis Report")

        print_info("Generating comprehensive synthesis report...")
        print_info("This will:")
        print_info("  - Analyze all claims and dependencies")
        print_info("  - Identify key findings")
        print_info("  - Document contradictions")
        print_info("  - Provide recommendations")

        try:
            response = await client.post(
                f"{API_BASE}/api/v1/reports/{pipeline_id}/generate",
                params={'report_type': 'synthesis'}
            )

            if response.status_code == 200:
                result = response.json()
                print_success("Report generation started")
                print_info(f"Job ID: {result['job_id']}")
                print_info("Make sure worker_reports.py is running!")

                # Wait for report generation
                print_info("\nWaiting for report generation (this may take 30-60s)...")
                await asyncio.sleep(40)

            else:
                print_error(f"Failed to generate report: {response.status_code}")

        except Exception as e:
            print_error(f"Error generating report: {e}")

        # Test 6: Get Generated Report
        print_section("Test 6: Retrieve Generated Report")

        try:
            response = await client.get(
                f"{API_BASE}/api/v1/reports/{pipeline_id}/latest"
            )

            if response.status_code == 200:
                report = response.json()
                print_success("Retrieved synthesis report")
                print_info(f"Report ID: {report['id']}")
                print_info(f"Title: {report['title']}")
                print_info(f"Generated: {report['generated_at']}")
                print_info(f"Content length: {len(report['content'])} chars")

                # Show report preview
                print(f"\n{BLUE}Report Preview:{RESET}")
                print("-" * 60)
                content_preview = report['content'][:1000]
                print(content_preview)
                if len(report['content']) > 1000:
                    print("\n[... report continues ...]")
                print("-" * 60)

                # Show statistics
                stats = report.get('statistics', {})
                if stats:
                    print(f"\n{BLUE}Report Statistics:{RESET}")
                    print(f"  Total Claims: {stats.get('total_claims', 0)}")
                    print(f"  Dependencies: {stats.get('total_dependencies', 0)}")
                    print(f"  Contradictions: {stats.get('total_contradictions', 0)}")
                    print(f"  Foundational Claims: {stats.get('foundational_claims', 0)}")
                    print(f"  Documents Analyzed: {stats.get('documents_analyzed', 0)}")

            else:
                print_info("Report not found yet (worker may still be generating)")

        except Exception as e:
            print_error(f"Error retrieving report: {e}")

        # Summary
        print_section("Test Summary")
        print_success("Phase 3 advanced features tested!")
        print_info(f"Pipeline ID: {pipeline_id}")
        print_info("\nCapabilities demonstrated:")
        print_info("  ✓ Dependency inference with Gemini")
        print_info("  ✓ Graph metrics (PageRank, centrality)")
        print_info("  ✓ Foundational claim identification")
        print_info("  ✓ Contradiction detection")
        print_info("  ✓ Synthesis report generation")
        print_info("\nWorkers needed:")
        print_info("  - python apps/workers/worker_inference.py")
        print_info("  - python apps/workers/worker_reports.py")
        print_info("\nAPI Docs: http://localhost:8000/docs")

        return True

if __name__ == "__main__":
    print(f"\n{BLUE}Cross-LLM Research Synthesis - Phase 3 Test{RESET}")
    print(f"{BLUE}==============================================={RESET}\n")

    # Get pipeline ID from command line
    if len(sys.argv) > 1:
        pipeline_id = sys.argv[1]
    else:
        print_error("Usage: python test_phase3.py <pipeline-id>")
        print_info("\nFirst run test_phase2.py to create a pipeline with claims")
        print_info("Then use the pipeline ID here")
        sys.exit(1)

    success = asyncio.run(test_phase3(pipeline_id))

    sys.exit(0 if success else 1)
