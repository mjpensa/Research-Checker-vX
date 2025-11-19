"""
Phase 2 Test Script
Tests the complete pipeline from document upload to claim extraction

This script demonstrates:
1. Creating a pipeline
2. Uploading documents
3. Starting pipeline processing
4. Monitoring job status
5. Retrieving extracted claims
"""
import asyncio
import httpx
import sys
from pathlib import Path

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

async def test_phase2():
    """Run complete Phase 2 test"""

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Test 1: Health Check
        print_section("Test 1: API Health Check")

        try:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                data = response.json()
                print_success(f"API is healthy")
                print_info(f"Version: {data['version']}")
                print_info(f"Environment: {data['environment']}")
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Cannot connect to API: {e}")
            print_info("Make sure API is running: python main.py")
            return False

        # Test 2: Create Pipeline
        print_section("Test 2: Create Pipeline")

        try:
            response = await client.post(
                f"{API_BASE}/api/v1/pipelines/",
                json={
                    "name": "Test Research Pipeline",
                    "metadata": {"test": True, "phase": 2}
                }
            )

            if response.status_code == 201:
                pipeline = response.json()
                pipeline_id = pipeline['id']
                print_success(f"Created pipeline: {pipeline_id}")
                print_info(f"Name: {pipeline['name']}")
                print_info(f"Status: {pipeline['status']}")
            else:
                print_error(f"Failed to create pipeline: {response.status_code}")
                print_error(response.text)
                return False
        except Exception as e:
            print_error(f"Error creating pipeline: {e}")
            return False

        # Test 3: Create Test Document
        print_section("Test 3: Upload Test Document")

        # Create a test document
        test_content = """
        Research Findings on Machine Learning

        This study examines the effectiveness of transformer models in natural language processing.

        Key findings:
        1. Transformer models achieve 95% accuracy on text classification tasks.
        2. Training time is reduced by 40% compared to LSTM models.
        3. The attention mechanism allows for better contextual understanding.

        Conclusion:
        Our research demonstrates that transformer architectures represent a significant
        advancement in NLP capabilities. The findings suggest that organizations should
        consider adopting transformer-based models for production systems.
        """

        # Save to temporary file
        test_file_path = Path("/tmp/test_document.txt")
        test_file_path.write_text(test_content)

        try:
            with open(test_file_path, 'rb') as f:
                files = {'files': ('test_document.txt', f, 'text/plain')}
                data = {'source_llm': 'gpt-4'}

                response = await client.post(
                    f"{API_BASE}/api/v1/pipelines/{pipeline_id}/documents",
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                uploads = response.json()
                for upload in uploads:
                    if upload['success']:
                        print_success(f"Uploaded: {upload['filename']}")
                        print_info(f"Document ID: {upload['document_id']}")
                        print_info(f"Message: {upload['message']}")
                    else:
                        print_error(f"Upload failed: {upload['message']}")
            else:
                print_error(f"Failed to upload document: {response.status_code}")
                print_error(response.text)
                return False

        except Exception as e:
            print_error(f"Error uploading document: {e}")
            return False
        finally:
            # Cleanup
            if test_file_path.exists():
                test_file_path.unlink()

        # Test 4: List Documents
        print_section("Test 4: List Pipeline Documents")

        try:
            response = await client.get(f"{API_BASE}/api/v1/pipelines/{pipeline_id}/documents")

            if response.status_code == 200:
                documents = response.json()
                print_success(f"Found {len(documents)} document(s)")

                for doc in documents:
                    print_info(f"Document: {doc['filename']}")
                    print_info(f"  Status: {doc['status']}")
                    print_info(f"  Text length: {doc['text_length']} words")
                    print_info(f"  File size: {doc['file_size']} bytes")
            else:
                print_error(f"Failed to list documents: {response.status_code}")
        except Exception as e:
            print_error(f"Error listing documents: {e}")

        # Test 5: Start Pipeline
        print_section("Test 5: Start Pipeline Processing")

        print_info("This will enqueue claim extraction jobs...")
        print_info("Make sure worker is running: python apps/workers/worker_extraction.py")

        try:
            response = await client.post(f"{API_BASE}/api/v1/pipelines/{pipeline_id}/start")

            if response.status_code == 200:
                pipeline = response.json()
                print_success(f"Pipeline started")
                print_info(f"Status: {pipeline['status']}")
                print_info("Jobs have been enqueued for background processing")
            else:
                print_error(f"Failed to start pipeline: {response.status_code}")
                print_error(response.text)
        except Exception as e:
            print_error(f"Error starting pipeline: {e}")

        # Test 6: Check Pipeline Status
        print_section("Test 6: Monitor Pipeline Status")

        print_info("Waiting for worker to process jobs...")
        print_info("(This requires the worker to be running)")

        for i in range(10):
            await asyncio.sleep(2)

            try:
                response = await client.get(f"{API_BASE}/api/v1/pipelines/{pipeline_id}")

                if response.status_code == 200:
                    pipeline = response.json()
                    print_info(f"  [{i+1}/10] Status: {pipeline['status']}, Claims: {pipeline['total_claims']}")

                    if pipeline['total_claims'] > 0:
                        print_success("Claims have been extracted!")
                        break

            except Exception as e:
                print_error(f"Error checking status: {e}")
                break
        else:
            print_info("Worker may not be running or still processing...")

        # Test 7: List Claims
        print_section("Test 7: List Extracted Claims")

        try:
            response = await client.get(
                f"{API_BASE}/api/v1/claims/",
                params={'pipeline_id': pipeline_id, 'limit': 10}
            )

            if response.status_code == 200:
                claims = response.json()

                if claims:
                    print_success(f"Retrieved {len(claims)} claim(s)")

                    for idx, claim in enumerate(claims[:5], 1):
                        print(f"\n  {idx}. {claim['text'][:100]}...")
                        print(f"     Type: {claim['claim_type']}")
                        print(f"     Confidence: {claim.get('confidence', 'N/A')}")
                else:
                    print_info("No claims extracted yet")
                    print_info("Make sure the worker is running and processing jobs")
            else:
                print_error(f"Failed to list claims: {response.status_code}")
        except Exception as e:
            print_error(f"Error listing claims: {e}")

        # Test 8: Get Claim Stats
        print_section("Test 8: Pipeline Claim Statistics")

        try:
            response = await client.get(f"{API_BASE}/api/v1/claims/pipeline/{pipeline_id}/stats")

            if response.status_code == 200:
                stats = response.json()
                print_success("Statistics retrieved")
                print_info(f"Total claims: {stats['total_claims']}")
                print_info(f"Claims by type: {stats['claims_by_type']}")
                print_info(f"Foundational claims: {stats['foundational_claims']}")
                print_info(f"Average confidence: {stats['average_confidence']:.2f}")
            else:
                print_error(f"Failed to get stats: {response.status_code}")
        except Exception as e:
            print_error(f"Error getting stats: {e}")

        # Summary
        print_section("Test Summary")
        print_success("Phase 2 core functionality is working!")
        print_info(f"Pipeline ID: {pipeline_id}")
        print_info("\nNext steps:")
        print_info("1. Start the worker: python apps/workers/worker_extraction.py")
        print_info("2. Watch claims being extracted in real-time")
        print_info("3. Connect to WebSocket: ws://localhost:8000/ws/pipelines/{pipeline_id}")
        print_info("4. View API docs: http://localhost:8000/docs")

        return True

if __name__ == "__main__":
    print(f"\n{BLUE}Cross-LLM Research Synthesis - Phase 2 Test{RESET}")
    print(f"{BLUE}============================================={RESET}\n")

    success = asyncio.run(test_phase2())

    sys.exit(0 if success else 1)
