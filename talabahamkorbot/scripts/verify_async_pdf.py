import asyncio
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import PdfService

async def tick():
    print("Tick loop started")
    for _ in range(5):
        start = time.time()
        await asyncio.sleep(0.1)
        diff = time.time() - start
        # If blocked, diff will be significantly larger than 0.1
        print(f"Tick: {diff:.4f}s")
        if diff > 0.5:
             print("⚠️  WARNING: Loop blocked!")

async def main():
    print("Testing PDF Generation NON-BLOCKING nature...")
    
    # Start tickers
    ticker = asyncio.create_task(tick())
    
    start_time = time.time()
    # Generate a heavy PDF
    print("Generating PDF...")
    # We use a loop of generation to make it heavy enough to notice blockage if it existed
    for _ in range(5):
        await PdfService.generate_reference_pdf(
            "Test Student " * 5, 
            "123456789", 
            "Information Technologies " * 5, 
            "Bachelor", 
            "3"
        )
    
    print(f"PDF Generation finished in {time.time() - start_time:.4f}s")
    await ticker
    print("Test Complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ImportError:
        print("Skipping test: Dependencies not passed or path issue")
    except Exception as e:
        print(f"Test Failed: {e}")
