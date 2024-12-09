from flask import Flask, request, Response
from functools import wraps
import os
import threading
import subprocess

app = Flask(__name__)

# Set your YouTube HLS stream key here
STREAM_KEY = "your-stream-key-here"

# Set username and password for BASIC HTTP authentication for /upload_segment
AUTH_USERNAME = 'admin'
AUTH_PASSWORD = 'secret'

# Segment "buffer" size, before ffmpeg starts
SEGMENT_BUFFER = 5

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

# Initialize the playlist
def initialize_playlist():
    global map_written, last_sequence, segment_count, segment_buffer
    
    map_written = False
    last_sequence = -1
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
    global last_sequence, segment_count, ffmpeg_process

    segment = request.files["segment"]  # Uploaded file
    duration = float(request.form["duration"])  # Segment duration
    sequence = int(request.form["sequence"])  # Sequence number
    is_init = request.form["is_init"].lower() == "true"  # Initialization flag

    segment_name = f"segment_{sequence:06d}.{'mp4' if is_init else 'm4s'}"
    segment_path = os.path.join(SEGMENTS_DIR, segment_name)

    # Save segment to file
    segment.save(segment_path)

    # Buffer the segment and update the playlist
    with playlist_lock:
        if is_init:
            # Reset everything for new stream
            if ffmpeg_process:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()
                ffmpeg_process = None 
            initialize_playlist()
            
        segment_buffer[sequence] = {
            "path": segment_name,
            "duration": duration,
            "is_init": is_init
        }
        update_playlist()
        
        # Increment segment counter and start ffmpeg if 30 segments have been uploaded
        segment_count += 1
        if segment_count == SEGMENT_BUFFER and not is_init:
            start_ffmpeg_relay()

    return "Segment uploaded", 200


# Update the playlist with buffered segments in sequence
def update_playlist():
    global last_sequence

    # Get the next sequence number to add
    next_sequence = min(segment_buffer.keys()) if segment_buffer else None

    while next_sequence is not None:
        segment = segment_buffer.pop(next_sequence)

        # Append to playlist
        append_segment_to_playlist(
            segment_name=segment["path"],
            duration=segment["duration"] if not segment["is_init"] else None,
            is_init=segment["is_init"]
        )

        last_sequence = next_sequence
        # Get the next sequence number to add from the remaining buffer
        next_sequence = min(segment_buffer.keys()) if segment_buffer else None


# Start the ffmpeg relay process
def start_ffmpeg_relay():
    global ffmpeg_process
    ffmpeg_command = [
        "ffmpeg", 
        "-live_start_index", "0", 
        "-i", PLAYLIST_FILE, 
        "-c", "copy",
        "-hls_init_time", "4.000", 
        "-hls_time", "4.000",
        "-strftime", "1", 
        "-master_pl_name", "master.m3u8", 
        "-http_persistent", "1",
        "-f", "hls", 
        "-method", "POST",
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
initialize_playlist()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
