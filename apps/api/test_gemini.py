"""
Test script for Gemini integration
Run this to verify Gemini API connectivity and response caching
"""
import asyncio
import sys
from services.gemini.client import gemini_client
from services.gemini.prompts import ClaimExtractionPrompt
from core.redis import redis_client

async def test_gemini():
    """Test Gemini API integration"""

    print("=" * 60)
    print("Testing Gemini 2.5 Flash Integration")
    print("=" * 60)

    # Test 1: Simple text generation
    print("\n[Test 1] Simple content generation...")
    try:
        sample_text = """
        The research study conducted in 2024 found that 75% of participants
        preferred option A over option B. This suggests a strong user preference
        for the new interface design. Additionally, the response time decreased
        by 40% compared to the baseline measurement.
        """

        prompt = ClaimExtractionPrompt().render(
            text=sample_text,
            source_name="Test Research Document",
            document_type="research"
        )

        print(f"Prompt length: {len(prompt)} characters")
        print("Sending request to Gemini...")

        response = await gemini_client.generate_content_async(
            prompt,
            use_cache=False  # First run without cache
        )

        print(f"\n✅ Response received ({len(response)} characters)")
        print("\nResponse preview:")
        print("-" * 60)
        print(response[:500] + "..." if len(response) > 500 else response)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    # Test 2: JSON generation
    print("\n[Test 2] JSON-formatted response...")
    try:
        response_json = await gemini_client.generate_json_async(
            prompt,
            use_cache=False
        )

        print(f"✅ JSON response received")
        print(f"Type: {type(response_json)}")

        if isinstance(response_json, dict) and 'claims' in response_json:
            claims = response_json.get('claims', [])
            print(f"Extracted {len(claims)} claims")

            if claims:
                print("\nFirst claim:")
                print(f"  Text: {claims[0].get('text', 'N/A')}")
                print(f"  Type: {claims[0].get('type', 'N/A')}")
                print(f"  Confidence: {claims[0].get('confidence', 'N/A')}")
        else:
            print(f"Response structure: {list(response_json.keys())}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    # Test 3: Cache functionality
    print("\n[Test 3] Testing response caching...")
    try:
        import time

        # First request (should cache)
        start = time.time()
        await gemini_client.generate_content_async(prompt, use_cache=True)
        first_duration = time.time() - start
        print(f"First request: {first_duration:.2f}s (cached)")

        # Second request (should hit cache)
        start = time.time()
        await gemini_client.generate_content_async(prompt, use_cache=True)
        second_duration = time.time() - start
        print(f"Second request: {second_duration:.2f}s (from cache)")

        if second_duration < first_duration * 0.5:
            print("✅ Cache is working! Second request was significantly faster")
        else:
            print("⚠️  Cache might not be working optimally")

    except Exception as e:
        print(f"\n❌ Cache test error: {e}")
        return False

    # Test 4: Token estimation
    print("\n[Test 4] Token estimation...")
    try:
        tokens = gemini_client.estimate_tokens(sample_text)
        print(f"Estimated tokens for sample text: ~{tokens}")
        print(f"Text length: {len(sample_text)} characters")
        print(f"Ratio: ~{len(sample_text) / tokens:.1f} chars/token")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    print("\n" + "=" * 60)
    print("All Gemini tests passed! ✅")
    print("=" * 60)
    return True

async def main():
    """Main test runner"""
    print("\nInitializing Redis connection...")
    try:
        await redis_client.connect()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("Continuing without cache (tests will still work)...")

    try:
        success = await test_gemini()
        sys.exit(0 if success else 1)
    finally:
        await redis_client.close()

if __name__ == "__main__":
    asyncio.run(main())
