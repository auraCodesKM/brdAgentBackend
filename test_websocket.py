import asyncio
import websockets
import json

async def test_stream():
    sections = ["functional_requirements", "executive_summary"]
    
    for section in sections:
        print(f"\n--- Streaming {section} ---")
        uri = f"ws://localhost:8000/api/generate/stream/{section}"
        try:
            async with websockets.connect(uri) as ws:
                # Send context/query as requested by the server logic
                await ws.send("")
                while True:
                    try:
                        token = await asyncio.wait_for(ws.recv(), timeout=30)
                        if token == "[ERROR]":
                            break
                        if token == "[DONE]":
                            break
                        print(token, end="", flush=True)
                    except asyncio.TimeoutError:
                        break
        except Exception as e:
            print(f"Error connecting to WebSocket for {section}: {e}")
            
    print("\n\nStream testing completed.")

if __name__ == "__main__":
    asyncio.run(test_stream())
