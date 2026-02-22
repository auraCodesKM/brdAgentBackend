import asyncio
import websockets
import json

async def fetch_section(section_name: str) -> str:
    uri = f"ws://localhost:8000/api/generate/stream/{section_name}"
    content = ""
    try:
        async with websockets.connect(uri, ping_timeout=None, ping_interval=None) as ws:
            # The backend listens for any string, but frontend sends "Generate..."
            await ws.send("Generate a comprehensive section for the BRD based directly on the provided unstructured corpus context.")
            print(f"[{section_name}] Connection established, awaiting stream...")
            
            async for message in ws:
                if message == "[DONE]" or '"type": "complete"' in message or "[ERROR]" in message:
                    break
                content += message
                print(message, end="", flush=True)
            print(f"\n[{section_name}] Stream Complete.\n")
    except Exception as e:
        print(f"[{section_name}] Error: {e}")
    return content

async def main():
    print("Fetching Timeline...")
    timeline_res = await fetch_section("timeline")
    
    with open("timeline_verification.md", "w", encoding="utf-8") as f:
        f.write("# Timeline Section Validation:\n\n")
        f.write(timeline_res)
        f.write("\n\n")

if __name__ == "__main__":
    asyncio.run(main())
