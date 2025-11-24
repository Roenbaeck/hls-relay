import requests
import time
import subprocess
import os
import shutil
import sys
import signal

# Configuration
RELAY_PORT = 8080
RELAY_URL = f"http://127.0.0.1:{RELAY_PORT}"
STREAM_KEY = "test_stream_restart"
AUTH = ('brute', 'force')

def start_relay():
    print("Starting relay...")
    if os.path.exists("segments"):
        shutil.rmtree("segments")
    
    process = subprocess.Popen(
        [sys.executable, "hls_relay.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    time.sleep(2)
    return process

def upload_segment(sequence, is_init=False, duration=2.0):
    headers = {
        "Target": "youtube", # Needs a target that triggers ffmpeg
        "Stream-Key": STREAM_KEY,
        "Segment-Type": "Initialization" if is_init else "Media",
        "Discontinuity": "false",
        "Duration": str(duration),
        "Sequence": str(sequence)
    }
    # We need real-ish data or ffmpeg might complain if it tries to read it?
    # Actually hls_relay serves what we upload.
    # If we upload junk, ffmpeg will fail to probe it.
    # We should probably upload small valid mp4s if possible, or just hope ffmpeg doesn't crash immediately on open.
    # But wait, if ffmpeg fails to open/probe, it will exit.
    # The user provided `reproduce_issue.py` used "dummy_content".
    # But that was for "passive" target where ffmpeg is NOT started.
    # Here we need ffmpeg to run.
    # If we use "dummy_content", ffmpeg will likely fail immediately.
    # We need valid content or at least something that keeps ffmpeg alive for a moment.
    # Or we can just check if it *tries* to open the segment.
    
    data = b"dummy_content"
    try:
        response = requests.post(f"{RELAY_URL}/upload_segment", headers=headers, data=data, auth=AUTH)
        return response
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

def kill_ffmpeg():
    print("Killing ffmpeg...")
    # Find ffmpeg process with our stream key
    cmd = f"pgrep -f 'ffmpeg.*{STREAM_KEY}'"
    try:
        pids = subprocess.check_output(cmd, shell=True).decode().strip().split()
        for pid in pids:
            os.kill(int(pid), signal.SIGKILL)
            print(f"Killed ffmpeg pid {pid}")
    except subprocess.CalledProcessError:
        print("No ffmpeg process found to kill")

def run_test():
    relay_proc = start_relay()
    
    # We need to read stdout in a non-blocking way or a separate thread to see logs
    import threading
    import queue
    log_queue = queue.Queue()
    
    def logger():
        for line in relay_proc.stdout:
            log_queue.put(line)
            # print(f"RELAY: {line.strip()}")
    
    t = threading.Thread(target=logger, daemon=True)
    t.start()

    try:
        print("Uploading init...")
        upload_segment(0, is_init=True, duration=0)
        
        print("Uploading segments 1-3...")
        for i in range(1, 4):
            upload_segment(i)
            time.sleep(0.5)
            
        # Wait for ffmpeg to start (it starts after 3 segments)
        time.sleep(2)
        
        print("Killing ffmpeg now!")
        kill_ffmpeg()
        time.sleep(1)
        
        print("Uploading segment 4 (should trigger restart)...")
        upload_segment(4)
        time.sleep(5)
        
        print("Uploading segment 5...")
        upload_segment(5)
        time.sleep(2)

    finally:
        relay_proc.terminate()
        relay_proc.wait()
        
    print("\n--- RELAY LOGS ---")
    while not log_queue.empty():
        line = log_queue.get()
        print(line.strip())

if __name__ == "__main__":
    run_test()
