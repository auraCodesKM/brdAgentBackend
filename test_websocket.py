import asyncio
import websockets

async def fetch_section(section_name: str) -> str:
    uri = f"ws://localhost:8001/api/generate/stream/{section_name}"
    content = ""
    try:
        async with websockets.connect(uri, ping_timeout=None, ping_interval=None) as ws:
            await ws.send("Generate a comprehensive section for the BRD based directly on the provided unstructured corpus context.")
            print(f"[{section_name}] Connection established, awaiting stream...")
            
            async for message in ws:
                if message == "[DONE]" or '"type": "complete"' in message or "[ERROR]" in message:
                    break
                content += message
            print(f"[{section_name}] Stream Complete.")
    except Exception as e:
        print(f"[{section_name}] Error: {e}")
    return content

async def main():
    sections = [
        "executive_summary",
        "business_objectives",
        "stakeholder_analysis",
        "functional_requirements",
        "non_functional_requirements",
        "assumptions",
        "success_metrics",
        "timeline"
    ]
    
    print("Fetching all 8 sections sequentially via WebSockets...")
    results = []
    for s in sections:
        res = await fetch_section(s)
        results.append(res)
    
    with open("full_audit_results.md", "w", encoding="utf-8") as f:
        f.write("# Full BRD Audit Results\n\n")
        for i, res in enumerate(results):
            f.write(f"\n\n## {sections[i].replace('_', ' ').title()}\n")
            f.write(res)
            f.write("\n\n---\n\n")
    print("Validation written to full_audit_results.md")

if __name__ == "__main__":
    asyncio.run(main())
