# Typical start command: 
# python -u hls_relay.py &> 20250119.log
from flask import Flask, request, Response
from functools import wraps
import os
import threading
import subprocess
import time
from datetime import datetime

# Set username and password for BASIC HTTP authentication for /upload_segment
AUTH_USERNAME = 'brute'
AUTH_PASSWORD = 'force'

# Port number to listen for incoming connections on, with 80 or 8080 being common choices
# Needs to be over 1024 if you are not a privileged user
PORT = 8080

# Base directory for all streams
BASE_SEGMENTS_DIR = "segments"

# Segment "buffer" size, before ffmpeg starts
SEGMENTS_BEFORE_RELAY = 3

# 60 seconds is roughly the time is takes for YouTube to time out if no data is received
MISSING_SEGMENT_TIMEOUT = 60

app = Flask(__name__)

# Ensure the base directory exists
os.makedirs(BASE_SEGMENTS_DIR, exist_ok=True)

# Dictionary to store stream-specific variables
stream_creation_lock = threading.Lock()
streams = {}

class StreamState:
    def __init__(self, stream_key):
        self.stream_key = stream_key
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stream_id = f"{stream_key}_{self.timestamp}"
        self.stream_dir = os.path.join(BASE_SEGMENTS_DIR, f"{self.stream_id}")
        os.makedirs(self.stream_dir, exist_ok=True)
        self.playlist_file = os.path.join(self.stream_dir, "playlist.m3u8")
        self.playlist_lock = threading.Lock()
        self.arrived_segments = {}  # Dictionary to store arrived segments, key=sequence
        self.last_playlist_sequence = -1 # Track the last sequence added to the playlist
        self.map_written = False
        self.written_segment_count = 0
        self.ffmpeg_process = None
        self.last_upload_time = time.time()
        self.check_missing_segments_started = False
        self.check_missing_segments_stop_event = threading.Event()

    def initialize_playlist(self, init_sequence, init_segment_name):
        print(f"Initializing playlist for stream {self.stream_id}")
        with open(self.playlist_file, "w") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:7\n")
            f.write("#EXT-X-TARGETDURATION:2\n")
            f.write(f"#EXT-X-MEDIA-SEQUENCE:{init_sequence}\n")
            f.write("#EXT-X-PLAYLIST-TYPE:EVENT\n")
            f.write(f"#EXT-X-MAP:URI=\"{init_segment_name}\"\n")
        self.map_written = True
        self.last_playlist_sequence = init_sequence - 1

    def finalize_playlist(self):
        print(f"Finalizing playlist for stream {self.stream_id}")
        try:
            with open(self.playlist_file, "a") as f:
                f.write("#EXT-X-ENDLIST\n")
        except Exception as e:
            print(f"Error in finalize_playlist: {e}")
        self.check_missing_segments_stop_event.set()
        self.check_missing_segments_started = False

        # Remove this finished stream from the global streams dictionary
        global streams
        with stream_creation_lock:
            # Only remove if this instance is still the one associated with its stream key
            if streams.get(self.stream_key) is self:
                del streams[self.stream_key]

    def check_missing_segments(self):
        while not self.check_missing_segments_stop_event.is_set():
            time.sleep(1)
            if time.time() - self.last_upload_time > MISSING_SEGMENT_TIMEOUT:
                print(f"Timeout for missing segments in stream {self.stream_dir}")
                self.finalize_playlist()
                break

    def start_ffmpeg_relay(self, target, stream_key, live_start_index=0):
        if target == "youtube":
            ffmpeg_command = [
                "ffmpeg",
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_on_network_error", "1",
                "-reconnect_on_http_error", "4xx,5xx",
                "-reconnect_delay_max", f"{MISSING_SEGMENT_TIMEOUT}",
                "-max_reload", f"{MISSING_SEGMENT_TIMEOUT}",
                "-m3u8_hold_counters", f"{MISSING_SEGMENT_TIMEOUT}",
                "-seg_max_retry", f"{MISSING_SEGMENT_TIMEOUT}",
                "-live_start_index", str(live_start_index),
                "-copyts",
                "-fflags", "+genpts",
                "-re",
                "-i", f"http://127.0.0.1:{PORT}/segments/{self.stream_id}/playlist.m3u8",
                "-c", "copy",
                "-fps_mode", "passthrough",
                "-master_pl_name", "master.m3u8",
                "-http_persistent", "1",
                "-f", "hls",
                "-hls_playlist_type", "event",
                "-hls_allow_cache", "1",
                "-method", "POST",
                f"https://a.upload.youtube.com/http_upload_hls?cid={stream_key}&copy=0&file=master.m3u8"
            ]
        elif target == "twitch":
            ffmpeg_command = [
                "ffmpeg",
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_on_network_error", "1",
                "-reconnect_on_http_error", "4xx,5xx",
                "-reconnect_delay_max", f"{MISSING_SEGMENT_TIMEOUT}",
                "-max_reload", f"{MISSING_SEGMENT_TIMEOUT}",
                "-m3u8_hold_counters", f"{MISSING_SEGMENT_TIMEOUT}",
                "-seg_max_retry", f"{MISSING_SEGMENT_TIMEOUT}",
                "-live_start_index", str(live_start_index),
                "-copyts",
                "-fflags", "+genpts",
                "-re",
                "-i", f"http://127.0.0.1:{PORT}/segments/{self.stream_id}/playlist.m3u8",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-b:v", "8M",
                "-pix_fmt", "yuv420p",
                "-bufsize", "16000k",
                "-g", "60",
                "-c:a", "copy",
                "-fps_mode", "passthrough",
                "-f", "flv",
                "-rtmp_buffer", "10000",
                f"rtmp://ingest.global-contribute.live-video.net/app/{stream_key}"
            ]
        else:
            raise ValueError(f"Unsupported target: {target}")

        print(f"Starting ffmpeg relay for stream {stream_key} to target {target} with live_start_index {live_start_index}")
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command)

    def update_playlist(self):
        while True:
            next_sequence = self.last_playlist_sequence + 1
            if next_sequence in self.arrived_segments:
                segment_info = self.arrived_segments.pop(next_sequence)
                segment_name = segment_info['filename']
                duration = segment_info['duration']
                is_init = segment_info['is_init']
                discontinuity = segment_info['discontinuity']

                with open(self.playlist_file, "a") as f:
                    if discontinuity:
                        f.write("#EXT-X-DISCONTINUITY\n")
                    if not is_init:
                        f.write(f"#EXTINF:{duration:.6f},\n")
                        f.write(f"{segment_name}\n")

                self.written_segment_count += 1
                self.last_playlist_sequence = next_sequence
            else:
                break
        # Check for finalization after processing segments
        if 'final' in self.arrived_segments:
            self.finalize_playlist()
            del self.arrived_segments['final']

# Rest of the authentication code remains the same
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

@app.route("/upload_segment", methods=["POST"])
@requires_auth
def upload_segment():
    required_headers = ["Target", "Stream-Key", "Segment-Type", "Discontinuity", "Duration", "Sequence"]
    missing_headers = [header for header in required_headers if request.headers.get(header) is None]
    if missing_headers:
        print(f"Missing headers: {', '.join(missing_headers)}")
        return f"Missing headers: {', '.join(missing_headers)}", 400

    try:
        header_target = request.headers.get("Target")
        header_stream_key = request.headers.get("Stream-Key")
        header_segment_type = request.headers.get("Segment-Type")
        header_discontinuity = request.headers.get("Discontinuity").lower() == "true"
        header_duration = float(request.headers.get("Duration"))
        header_sequence = int(request.headers.get("Sequence"))
    except ValueError as e:
        return f"Invalid header data: {e}", 400

    is_init = header_segment_type == "Initialization"
    is_final = header_segment_type == "Finalization"

    if header_duration == 0 and not is_init:
        return "Zero-duration segment ignored.", 200

    with stream_creation_lock:
        if header_stream_key not in streams:
            streams[header_stream_key] = StreamState(header_stream_key)
        stream = streams[header_stream_key]

    segment_name = f"segment_{header_sequence:06d}.{'mp4' if is_init else 'm4s'}"
    segment_path = os.path.join(stream.stream_dir, segment_name)

    try:
        with open(segment_path, "wb") as f:
            f.write(request.data)
    except Exception as e:
        return f"Error saving segment: {e}", 500
    
    print(f"Saved segment: {segment_name} for stream: {stream.stream_id}")

    stream.last_upload_time = time.time()
    # Start missing segments check thread
    if not stream.check_missing_segments_started:
        if not stream.check_missing_segments_started:
            stream.check_missing_segments_stop_event.clear()
            threading.Thread(target=stream.check_missing_segments, daemon=True).start()
            stream.check_missing_segments_started = True

    with stream.playlist_lock:
        if is_init:
            if stream.ffmpeg_process:
                stream.ffmpeg_process.terminate()
                stream.ffmpeg_process.wait()
                stream.ffmpeg_process = None
            stream.initialize_playlist(header_sequence, segment_name)

        stream.arrived_segments[header_sequence] = {
            "filename": segment_name,
            "duration": header_duration,
            "is_init": is_init,
            "discontinuity": header_discontinuity
        }
        if is_final:
            stream.arrived_segments['final'] = True # Use a simple flag for finalization

        stream.update_playlist()

        if stream.written_segment_count >= SEGMENTS_BEFORE_RELAY:
            if stream.written_segment_count == SEGMENTS_BEFORE_RELAY:
                print(f"Starting ffmpeg for stream {stream.stream_id} with {SEGMENTS_BEFORE_RELAY} buffered segments")
                stream.start_ffmpeg_relay(header_target, header_stream_key)
            elif stream.ffmpeg_process is None or stream.ffmpeg_process.poll() is not None:
                print(f"Restarting ffmpeg for stream {stream.stream_id} with live_start_index {stream.last_playlist_sequence + 1}")
                stream.start_ffmpeg_relay(header_target, header_stream_key, live_start_index=stream.last_playlist_sequence + 1)

    return "Segment uploaded", 200

@app.route("/segments/<stream_id>/playlist.m3u8")
def serve_playlist(stream_id):
    if request.remote_addr != '127.0.0.1' and request.remote_addr != '::1':
        return "Access denied", 403

    playlist_file = os.path.join("segments", stream_id, "playlist.m3u8")

    if not os.path.exists(playlist_file):
        return "Stream not found", 404

    def generate_playlist():
        with open(playlist_file, "r") as f:
            yield f.read()

    return Response(generate_playlist(), mimetype="application/vnd.apple.mpegurl")

@app.route("/segments/<stream_id>/<segment_name>")
def serve_segment(stream_id, segment_name):
    if request.remote_addr != '127.0.0.1' and request.remote_addr != '::1':
        return "Access denied", 403

    segment_path = os.path.join("segments", stream_id, segment_name)

    if not os.path.exists(segment_path):
        return "Segment not found", 404

    return Response(open(segment_path, "rb"), mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)