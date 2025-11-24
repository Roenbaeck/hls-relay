import requests
import time
import subprocess
import os
import shutil
import sys

# Configuration
RELAY_PORT = 8080
RELAY_URL = f"http://127.0.0.1:{RELAY_PORT}"
STREAM_KEY = "test_stream"
AUTH = ('brute', 'force')

def start_relay():
    print("Starting relay...")
    # Clean up segments directory
    if os.path.exists("segments"):
        shutil.rmtree("segments")
    
    # Start relay process
    process = subprocess.Popen(
        [sys.executable, "hls_relay.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(2) # Wait for startup
    return process

def upload_segment(sequence, is_init=False, duration=2.0):
    headers = {
        "Target": "passive",
        "Stream-Key": STREAM_KEY,
        "Segment-Type": "Initialization" if is_init else "Media",
        "Discontinuity": "false",
        "Duration": str(duration),
        "Sequence": str(sequence)
    }
    data = b"dummy_content"
    response = requests.post(f"{RELAY_URL}/upload_segment", headers=headers, data=data, auth=AUTH)
    return response

def count_directories():
    if not os.path.exists("segments"):
        return 0
    return len([d for d in os.listdir("segments") if d.startswith(STREAM_KEY)])

def run_test():
    relay_proc = start_relay()
    try:
        print("Uploading segment 0 (init)...")
        upload_segment(0, is_init=True, duration=0)
        
        print("Uploading segment 1...")
        upload_segment(1)
        
        print("Uploading segment 2...")
        upload_segment(2)
        
        initial_dirs = count_directories()
        print(f"Directories after initial segments: {initial_dirs}")
        if initial_dirs != 1:
            print("FAIL: Should have 1 directory")
            return

        print("Waiting for timeout (65s)...")
        time.sleep(65)
        
        print("Uploading segment 3 (late)...")
        upload_segment(3)
        
        final_dirs = count_directories()
        print(f"Directories after late segment: {final_dirs}")
        
        if final_dirs > 1:
            print("FAIL: Created a new directory for continuation segment!")
        else:
            print("SUCCESS: Kept same directory.")

    finally:
        relay_proc.terminate()
        relay_proc.wait()
        # print(relay_proc.stdout.read())

if __name__ == "__main__":
    run_test()
