import asyncio
import sys
import os
import uuid

# Add the 'Backend' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Backend')))

from main import LangGraphAgenticAI


async def run_tests():
    ai_system = LangGraphAgenticAI(debug=True)

    # Test Query 1: Summarize Chapter 3
    query1 = "Summarize Chapter 3 of the Virginia Building Code"
    thread_id1 = f"test_chapter_summary_{uuid.uuid4()}"
    print(f"\n--- Running Test Query 1: {query1} ---")
    result1 = await ai_system.invoke_for_test_async(query1, thread_id1)
    print("\nResult 1 (Chapter Summary):")
    print(result1.get("final_answer", "No final answer found."))
    print("\nFull State 1:")
    # print(result1) # Uncomment for full state debugging

    # Test Query 2: Technical Calculation
    query2 = "I am designing an office building with interior beams, each supporting a tributary area of 500 square feet. The unreduced live load (Lo) for offices is 50 psf. According to Section 1607.12.1, am I permitted to reduce the live load for these beams? If so, what is the final reduced design live load (L) in psf after applying Equation 16-7?"
    thread_id2 = f"test_technical_calculation_{uuid.uuid4()}"
    print(f"\n--- Running Test Query 2: {query2} ---")
    result2 = await ai_system.invoke_for_test_async(query2, thread_id2)
    print("\nResult 2 (Technical Calculation):")
    print(result2.get("final_answer", "No final answer found."))
    print("\nFull State 2:")
    # print(result2) # Uncomment for full state debugging

if __name__ == "__main__":
    asyncio.run(run_tests())

