from flask import Flask, request, Response
from functools import wraps
import os
import threading
import subprocess
import time

MISSING_SEGMENT_TIMEOUT = 60  # seconds

app = Flask(__name__)

# Set your YouTube HLS stream key here
STREAM_KEY = "your-stream-key-here"

# Set username and password for BASIC HTTP authentication for /upload_segment
AUTH_USERNAME = 'admin'
AUTH_PASSWORD = 'secret'

# Segment "buffer" size, before ffmpeg starts
SEGMENTS_BEFORE_RELAY = 5

# Directory to save segments and playlist
SEGMENTS_DIR = "segments"
PLAYLIST_FILE = os.path.join(SEGMENTS_DIR, "playlist.m3u8")

# Ensure the directory exists
os.makedirs(SEGMENTS_DIR, exist_ok=True)

# Sequence management
playlist_lock = threading.Lock()
segment_buffer = {}
last_sequence = -1  # Last sequence added to the playlist
map_written = False  # Flag to track if #EXT-X-MAP has been written
segment_count = 0  # Counter for uploaded segments
ffmpeg_process = None # Variable to hold the ffmpeg process
last_upload_time = time.time()
check_missing_segments_started = False
check_missing_segments_stop_event = threading.Event()

# Initialize the playlist
def initialize_playlist(sequence):
    global map_written, last_sequence, segment_count, segment_buffer
    
    map_written = False
    last_sequence = sequence - 1
    segment_count = 0
    segment_buffer = {}
    
    with open(PLAYLIST_FILE, "w") as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:7\n")  # Version 7 for fMP4
        f.write("#EXT-X-TARGETDURATION:2\n")  # Adjust as needed
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        f.write("#EXT-X-PLAYLIST-TYPE:EVENT\n")

# Append an initialization segment or media segment to the playlist
def append_segment_to_playlist(segment_name, duration=None, is_init=False):
    global map_written

    with open(PLAYLIST_FILE, "a") as f:
        if is_init and not map_written:
            # Write EXT-X-MAP only once
            f.write(f"#EXT-X-MAP:URI=\"{segment_name}\"\n")
            map_written = True
        elif duration is not None:
            # Write media segment
            f.write(f"#EXTINF:{duration:.6f},\n")
            f.write(f"{segment_name}\n")
        f.flush()  # Ensure data is written immediately

def finalize_playlist():
    global check_missing_segments_started, check_missing_segments_stop_event
    with open(PLAYLIST_FILE, "a") as f:
        f.write("#EXT-X-ENDLIST\n")
        # Signal the thread to stop and reset the flag
        check_missing_segments_stop_event.set()
        check_missing_segments_started = False

def check_missing_segments():
    global last_upload_time, ffmpeg_process, check_missing_segments_stop_event

    while not check_missing_segments_stop_event.is_set():
        time.sleep(1)
        with playlist_lock:
            if segment_buffer and (time.time() - last_upload_time > MISSING_SEGMENT_TIMEOUT):
                print("Timeout for missing segments. Finalizing playlist.")
                finalize_playlist()
                if ffmpeg_process:
                    ffmpeg_process.terminate()
                    ffmpeg_process.wait()
                    ffmpeg_process = None
                break

# Basic authentication
def check_auth(username, password):
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

def authenticate():
    return Response(        
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})
                            
def requires_auth(f):       
    @wraps(f)               
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated 

# Handle single segment upload
@app.route("/upload_segment", methods=["POST"])
@requires_auth 
def upload_segment():
    global last_sequence, segment_count, ffmpeg_process, last_upload_time, check_missing_segments_started, check_missing_segments_stop_event

    # Verify required headers are present
    required_headers = ["Initialization", "Discontinuity", "Duration", "Sequence"]
    missing_headers = [header for header in required_headers if request.headers.get(header) is None]

    if missing_headers:
        print(f"Missing headers: {', '.join(missing_headers)}")
        return f"Missing headers: {', '.join(missing_headers)}", 400
    
    # Extract data from the headers
    try:
        header_Initialization = request.headers.get("Initialization")
        header_Discontinuity = request.headers.get("Discontinuity")
        header_Duration = request.headers.get("Duration")
        header_Sequence = request.headers.get("Sequence")

        is_init = header_Initialization.lower() == "true"
        discontinuity = header_Discontinuity.lower() == "true"
        duration = float(header_Duration)
        sequence = int(header_Sequence)
    except ValueError as e:
        print(f"Error parsing header data: {e}")
        return "Invalid header data", 400
    
    # Now, request.data contains the body as bytes
    segment_data = request.data

    if duration == 0 and not is_init:
        print("Warning: Received zero-duration segment. Ignoring.")
        return "Zero-duration segment ignored.", 200

    last_upload_time = time.time()
    # Start the missing segments check thread on the first upload
    if not check_missing_segments_started:
        with playlist_lock:  # Ensure thread-safe initialization
            if not check_missing_segments_started:  # Double-check inside lock
                # Reset the stop event for the new thread
                check_missing_segments_stop_event.clear()
                threading.Thread(target=check_missing_segments, daemon=True).start()
                check_missing_segments_started = True

    segment_name = f"segment_{sequence:06d}.{'mp4' if is_init else 'm4s'}"
    segment_path = os.path.join(SEGMENTS_DIR, segment_name)

    # Save segment data to file
    try:
      with open(segment_path, "wb") as f:
        f.write(segment_data)
    except Exception as e:
        print(f"Error saving segment: {e}")
        return "Error saving segment", 500

    # Buffer the segment and update the playlist
    with playlist_lock:
        if is_init:
            # Reset everything for new stream
            if ffmpeg_process:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()
                ffmpeg_process = None 
            initialize_playlist(sequence)
            
        segment_buffer[sequence] = {
            "path": segment_name,
            "duration": duration,
            "is_init": is_init, 
            "discontinuity": discontinuity
        }
        update_playlist()
        
        # Increment segment counter and start ffmpeg if 30 segments have been uploaded
        segment_count += 1
        if segment_count == SEGMENTS_BEFORE_RELAY and not is_init:
            start_ffmpeg_relay()

    return "Segment uploaded", 200


# Update the playlist with buffered segments in sequence
def update_playlist():
    global last_sequence

    # Sort segments by sequence number
    sorted_segments = sorted(segment_buffer.items())
    processed_sequences = []

    for sequence, segment in sorted_segments:
        if sequence > last_sequence + 1:  # Gap Detected
            # Check if the current segment indicates a discontinuity
            if segment["discontinuity"]:
               with open(PLAYLIST_FILE, "a") as f:
                  f.write("#EXT-X-DISCONTINUITY\n")
            else:
                # We are waiting for segments to fill in the gap, so break out of loop
               break
        
        # Append to playlist
        append_segment_to_playlist(
            segment_name=segment["path"],
            duration=segment["duration"] if not segment["is_init"] else None,
            is_init=segment["is_init"]
        )
        
        # Update last sequence
        last_sequence = sequence
        processed_sequences.append(sequence)

    # remove processed segments
    for sequence in processed_sequences:
        del segment_buffer[sequence]

# Start the ffmpeg relay process
def start_ffmpeg_relay():
    global ffmpeg_process
    ffmpeg_command = [
        "ffmpeg",  
        "-live_start_index", "0",           # Set the starting index for live streams to 0. This can resolve initial sync issues.
        "-vsync", "0",                      # Disable video sync. This can improve performance, but may cause audio to drift out of sync with video.
        "-copyts",                          # Copy timestamps from input to output, preserving original timing.
        "-fflags", "+genpts",               # Generate presentation timestamps if they are missing in the input. Important for correct synchronization.
        "-re",                              # Read input at the native frame rate, avoiding reading too fast. Helps with live input stability.
        "-i", PLAYLIST_FILE,                # Input file is the dynamically generated HLS playlist
        "-c", "copy",                       # Copy all input streams directly without re-encoding. This reduces CPU usage and avoids potential quality loss.
        "-avoid_negative_ts", "make_zero",  # Adjusts negative timestamp values to start at zero. Fixes potential timestamp issues
        "-master_pl_name", "master.m3u8",   # Sets the name for the master playlist file
        "-http_persistent", "1",            # Enable persistent HTTP connections. This can improve performance.
        "-f", "hls",                        # Output format is HLS (HTTP Live Streaming)
        "-hls_playlist_type", "event",      # Sets the HLS playlist type to event, which means it's a live stream.
        "-hls_allow_cache", "1",            # Allow caching of segments by the client. May be useful for fault tolerance.
        "-method", "POST",                  # Specifies that the HLS segments should be sent via HTTP POST requests.
        f"https://a.upload.youtube.com/http_upload_hls?cid={STREAM_KEY}&copy=0&file=master.m3u8"
    ]
    print(f"Starting ffmpeg relay")
    ffmpeg_process = subprocess.Popen(ffmpeg_command)

# Serve the M3U8 playlist
@app.route("/segments/playlist.m3u8")
def serve_playlist():
    if request.remote_addr != '127.0.0.1' and request.remote_addr != '::1': 
        return "Access denied", 403

    def generate_playlist():
        with open(PLAYLIST_FILE, "r") as f:
            yield f.read()
    return Response(generate_playlist(), mimetype="application/x-mpegURL")


# Serve fMP4 segments       
@app.route("/segments/<segment_name>")
def serve_segment(segment_name):
    if request.remote_addr != '127.0.0.1' and request.remote_addr != '::1': 
        return "Access denied", 403

    segment_path = os.path.join(SEGMENTS_DIR, segment_name)
    if os.path.exists(segment_path):
        return Response(open(segment_path, "rb"), mimetype="video/mp4")
    else:
        return "Segment not found", 404


# Initialize the playlist at startup
initialize_playlist(last_sequence)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
