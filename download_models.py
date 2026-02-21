import os
from dotenv import load_dotenv

# Load environment variables from .env to keep the token completely secure
load_dotenv()

# Force the HuggingFace cache down to our local repo folder BEFORE importing huggingface_hub
hf_home = os.getenv("HF_HOME", "./hf_cache")
os.environ["HF_HOME"] = os.path.abspath(hf_home)

from huggingface_hub import login, snapshot_download

def main():
    print(f"\n==============================================")
    print(f"🚀 BRD Agent Model Setup")
    print(f"📁 Cache Directory: {os.environ['HF_HOME']}")
    print(f"==============================================\n")
    
    # Authenticate securely using the .env file
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("✅ Found HF_TOKEN in .env. Logging in to HuggingFace...")
        login(token=hf_token)
    else:
        print("⚠️ WARNING: HF_TOKEN not found in .env. Downloading unauthenticated.")
        print("⚠️ This will slow down downloads and may fail for gated models.")
        print("⚠️ Please add HF_TOKEN=your_token to your .env file and re-run.\n")

    models_to_download = [
        "BAAI/bge-m3",
        "BAAI/bge-reranker-large",
        "Systran/faster-whisper-large-v3",
        "Qwen/Qwen2.5-32B-Instruct-AWQ" # Using the VRAM-safe 32B model
    ]

    print(f"\nInitiating download of {len(models_to_download)} core models...")
    print(f"This may take 30-45 minutes depending on your internet connection.\n")

    for model in models_to_download:
        print(f"----------------------------------------------")
        print(f"⏳ Downloading: {model}")
        print(f"----------------------------------------------")
        try:
            # We filter out PyTorch/Flax binaries since we use vLLM/AWQ or specific loaders
            # But to be completely safe and avoid missing files, we will download everything.
            cache_path = snapshot_download(repo_id=model)
            print(f"✅ Success! {model} is cached and ready.")
        except Exception as e:
            print(f"❌ ERROR downloading {model}: {str(e)}")
            print("Please check your internet connection and HF_TOKEN.\n")

    print(f"\n==============================================")
    print(f"🎉 All models downloaded successfully!")
    print(f"You may now proceed to start the FastAPI server.")
    print(f"==============================================\n")

if __name__ == "__main__":
    main()
