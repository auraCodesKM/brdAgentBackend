import os
import glob
import time
import requests
import json

# Configuration
EMAILS_DIR = r"c:\Users\kevin\Desktop\brdA\brdAgentBackend\data\emails"
API_URL = "http://127.0.0.1:8001/ingest/email"
STATS_URL = "http://127.0.0.1:8001/cache/stats"
KEYWORDS = [
    "requirement", "deadline", "budget", "security", "performance", 
    "SSO", "audit", "concurrent", "dashboard", "mobile"
]
MAX_EMAILS = 50
BATCH_SIZE = 5
MAX_RUNTIME_MINUTES = 10

def get_matching_texts():
    print(f"Scanning {EMAILS_DIR} for matching emails...")
    matching_texts = []
    
    # Try all typical text files
    for filepath in glob.glob(os.path.join(EMAILS_DIR, "**", "*"), recursive=True):
        if len(matching_texts) >= MAX_EMAILS:
            break
            
        if not os.path.isfile(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # If it's a massive CSV chunk, split it somewhat
                if filepath.endswith('.csv'):
                    import csv
                    from io import StringIO
                    reader = csv.reader(StringIO(content))
                    for row in reader:
                        if len(matching_texts) >= MAX_EMAILS:
                            break
                        row_text = " ".join(row)
                        lower_content = row_text.lower()
                        if any(keyword.lower() in lower_content for keyword in KEYWORDS):
                            matching_texts.append(row_text)
                else:
                    lower_content = content.lower()
                    if any(keyword.lower() in lower_content for keyword in KEYWORDS):
                        matching_texts.append(content)
        except Exception:
            pass
            
    print(f"Found {len(matching_texts)} matching emails.")
    return matching_texts

def main():
    start_time = time.time()
    max_duration = MAX_RUNTIME_MINUTES * 60
    
    # 1. Gather texts
    texts_to_process = get_matching_texts()
    if not texts_to_process:
        print("No emails found. Exiting.")
        return
        
    # Wait for the API to be available
    print("Waiting for FastAPI server to come online...")
    while True:
        if time.time() - start_time > max_duration:
            print("Time limit reached while waiting for server.")
            return
            
        try:
            res = requests.get("http://127.0.0.1:8001/health")
            if res.status_code == 200:
                print("Server is online!")
                break
        except requests.exceptions.ConnectionError:
            pass
            
        time.sleep(2)
        
    print(f"Starting ingestion of {len(texts_to_process)} emails in batches of {BATCH_SIZE}...")
    
    processed_count = 0
    
    # Process in batches
    for i in range(0, len(texts_to_process), BATCH_SIZE):
        if time.time() - start_time > max_duration:
            print(f"Time limit of {MAX_RUNTIME_MINUTES} minutes reached. Stopping early.")
            break
            
        batch = texts_to_process[i:i + BATCH_SIZE]
        print(f"\nProcessing batch {i//BATCH_SIZE + 1} ({len(batch)} emails)...")
        
        for email_content in batch:
            try:
                response = requests.post(
                    API_URL, 
                    json={"text": email_content[:8000]}, # Hard safety limit for payload sizes
                    timeout=120
                )
                
                if response.status_code == 200:
                    processed_count += 1
                else:
                    print(f"Failed to ingest {os.path.basename(filepath)}: {response.text}")
                    
            except Exception as e:
                print(f"Error reading or posting {os.path.basename(filepath)}: {e}")
                
        # Print stats every 10 emails
        if processed_count > 0 and processed_count % 10 == 0:
            print(f"\n--- Progress: {processed_count} emails ingested ---")
            try:
                stats = requests.get(STATS_URL).json()
                print(f"Graph Database Cache Stats:")
                print(json.dumps(stats, indent=2))
            except Exception as e:
                print("Could not fetch stats.")
                
        # Delay 1 second between batches
        time.sleep(1)
        
    print(f"\nFinished! Successfully ingested {processed_count} emails.")
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
