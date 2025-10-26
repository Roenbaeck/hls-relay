# Typical start command: 
# python -u hls_relay.py &> 20250119.log
from flask import Flask, request, Response, jsonify
from functools import wraps
from collections import deque
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

# Timeout for skipping missing segments when new segments are arriving
GAP_SKIP_TIMEOUT = 10

# Sliding window (seconds) for measuring upload utilization
UPLOAD_UTIL_WINDOW = 60

# Maximum number of recent events to record per stream
MAX_EVENT_HISTORY = 20

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
        self.last_add_time = time.time()
        self.check_missing_segments_started = False
        self.check_missing_segments_stop_event = threading.Event()
        self.period_index = 0  # increments when a new init arrives after stream started
        # Gap handling state
        self._gap_wait_seq = None
        self._gap_wait_start = None
        self.finalized = False
        self.upload_history = deque()
        self.events = deque(maxlen=MAX_EVENT_HISTORY)
        self.last_ffmpeg_exit = None
        self.add_event("Stream state created")
        self.ffmpeg_log_thread = None

    def initialize_playlist(self, init_sequence, init_segment_name):
        print(f"Initializing playlist for stream {self.stream_id}", flush=True)
        with open(self.playlist_file, "w") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:7\n")
            f.write("#EXT-X-TARGETDURATION:2\n")
            f.write(f"#EXT-X-MEDIA-SEQUENCE:{init_sequence}\n")
            f.write("#EXT-X-PLAYLIST-TYPE:EVENT\n")
            f.write(f"#EXT-X-MAP:URI=\"{init_segment_name}\"\n")
        self.map_written = True
        self.last_playlist_sequence = init_sequence - 1
        self.add_event(f"Playlist initialized at sequence {init_sequence}")

    def finalize_playlist(self):
        print(f"Finalizing playlist for stream {self.stream_id}", flush=True)
        if self.finalized:
            return
        self.finalized = True
        self.add_event("Playlist finalized")
        try:
            with open(self.playlist_file, "a") as f:
                f.write("#EXT-X-ENDLIST\n")
        except Exception as e:
            print(f"Error in finalize_playlist: {e}", flush=True)
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
            if time.time() - self.last_upload_time > MISSING_SEGMENT_TIMEOUT or time.time() - self.last_add_time > MISSING_SEGMENT_TIMEOUT:
                print(f"Timeout for missing segments in stream {self.stream_dir}", flush=True)
                self.finalize_playlist()
                break

    def start_ffmpeg_relay(self, target, stream_key, live_start_index=None):
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
            ] + ([] if live_start_index is None else [
                "-live_start_index", str(live_start_index)
            ]) + [
                "-copyts",
                "-fflags", "+igndts",
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
            ] + ([] if live_start_index is None else [
                "-live_start_index", str(live_start_index)
            ]) + [
                "-copyts",
                "-fflags", "+igndts",
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

        start_desc = "edge" if live_start_index is None else str(live_start_index)
        print(f"Starting ffmpeg relay for stream {stream_key} to target {target} with live_start_index {start_desc}", flush=True)
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._start_ffmpeg_logger()
        self.add_event(f"ffmpeg started for {target} (start_index={start_desc})")

    def update_playlist(self):
        added = False
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

                # Only count media segments toward the buffer threshold
                if not is_init:
                    self.written_segment_count += 1
                self.last_playlist_sequence = next_sequence
                added = True
                # Reset any gap wait state
                self._gap_wait_seq = None
                self._gap_wait_start = None
                continue

            # Missing next_sequence
            now = time.time()
            if self._gap_wait_seq != next_sequence:
                # Start waiting for this specific sequence
                self._gap_wait_seq = next_sequence
                self._gap_wait_start = now
                break  # Exit; will be called again on next upload

            # Already waiting for this sequence; decide to skip?
            waited = now - (self._gap_wait_start or now)
            if waited >= GAP_SKIP_TIMEOUT:
                # Find the next available higher sequence
                candidates = [seq for seq in self.arrived_segments if isinstance(seq, int) and seq > self.last_playlist_sequence]
                if not candidates:
                    break
                next_seq = min(candidates)
                segment_info = self.arrived_segments.pop(next_seq)
                segment_name = segment_info['filename']
                duration = segment_info['duration']
                is_init = segment_info['is_init']

                with open(self.playlist_file, "a") as f:
                    # Only write discontinuity for media segments, never for init segments
                    if not is_init:
                        f.write("#EXT-X-DISCONTINUITY\n")
                        f.write(f"#EXTINF:{duration:.6f},\n")
                        f.write(f"{segment_name}\n")

                if not is_init:
                    self.written_segment_count += 1
                self.last_playlist_sequence = next_seq
                added = True
                self.add_event(f"Skipped sequence {next_sequence}; resumed at {next_seq}")
                # Reset or continue loop to handle more available sequences
                self._gap_wait_seq = None
                self._gap_wait_start = None
                continue

            # Haven't waited long enough; exit quickly to avoid blocking
            break

        if added:
            self.last_add_time = time.time()
        # Finalization flag
        if 'final' in self.arrived_segments:
            self.finalize_playlist()
            del self.arrived_segments['final']

    def record_upload_duration(self, duration):
        now = time.time()
        self.upload_history.append((now, duration))
        cutoff = now - UPLOAD_UTIL_WINDOW
        while self.upload_history and self.upload_history[0][0] < cutoff:
            self.upload_history.popleft()

    def add_event(self, message):
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.events.append({"time": timestamp, "message": message})

    def _start_ffmpeg_logger(self):
        if not self.ffmpeg_process or self.ffmpeg_process.stdout is None:
            return
        prefix = f"[ffmpeg {self.stream_id}] "

        def _pump():
            for line in self.ffmpeg_process.stdout:
                print(prefix + line.rstrip(), flush=True)
            try:
                self.ffmpeg_process.stdout.close()
            except Exception:
                pass

        self.ffmpeg_log_thread = threading.Thread(target=_pump, daemon=True)
        self.ffmpeg_log_thread.start()

    def _stop_ffmpeg_logger(self):
        if self.ffmpeg_log_thread:
            self.ffmpeg_log_thread.join(timeout=1)
        self.ffmpeg_log_thread = None

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
    request_start = time.perf_counter()
    required_headers = ["Target", "Stream-Key", "Segment-Type", "Discontinuity", "Duration", "Sequence"]
    missing_headers = [header for header in required_headers if request.headers.get(header) is None]
    if missing_headers:
        print(f"Missing headers: {', '.join(missing_headers)}", flush=True)
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

    old_stream = None
    with stream_creation_lock:
        stream = streams.get(header_stream_key)
        need_new_stream = False
        if stream is None or stream.finalized:
            need_new_stream = True
        elif is_init and stream.map_written and header_sequence <= stream.last_playlist_sequence:
            # Sequence number reset; treat as a brand new stream session
            need_new_stream = True
        if need_new_stream:
            old_stream = stream
            stream = StreamState(header_stream_key)
            streams[header_stream_key] = stream
        else:
            streams[header_stream_key] = stream

    if old_stream is not None:
        old_stream.check_missing_segments_stop_event.set()
        if old_stream.ffmpeg_process:
                proc = old_stream.ffmpeg_process
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    exit_code = proc.returncode
                    old_stream.add_event(f"ffmpeg exited with code {exit_code}")
                    old_stream.last_ffmpeg_exit = {"code": exit_code, "signal": None}
                except subprocess.TimeoutExpired:
                    print(f"Warning: ffmpeg did not exit in time for old stream {old_stream.stream_id}; killing", flush=True)
                    proc.kill()
                    proc.wait()
                    old_stream.add_event("ffmpeg killed after timeout")
                    old_stream.last_ffmpeg_exit = {"code": None, "signal": "SIGKILL"}
                except Exception as e:
                    print(f"Warning: failed to terminate ffmpeg for old stream {old_stream.stream_id}: {e}", flush=True)
                    old_stream.add_event(f"ffmpeg termination failed: {e}")
                    old_stream.last_ffmpeg_exit = {"code": None, "signal": str(e)}
                finally:
                    old_stream.ffmpeg_process = None
                    old_stream._stop_ffmpeg_logger()
        if not old_stream.finalized:
            old_stream.finalize_playlist()

    segment_name = f"p{stream.period_index}_segment_{header_sequence:06d}.{'mp4' if is_init else 'm4s'}"
    segment_path = os.path.join(stream.stream_dir, segment_name)

    try:
        with open(segment_path, "wb") as f:
            f.write(request.data)
    except Exception as e:
        return f"Error saving segment: {e}", 500
    
    print(f"Saved segment: {segment_name} for stream: {stream.stream_id}", flush=True)

    stream.last_upload_time = time.time()
    # Start missing segments check thread
    if not stream.check_missing_segments_started:
        if not stream.check_missing_segments_started:
            stream.check_missing_segments_stop_event.clear()
            threading.Thread(target=stream.check_missing_segments, daemon=True).start()
            stream.check_missing_segments_started = True

    with stream.playlist_lock:
        if is_init:
            if not stream.map_written:
                # First init: start playlist fresh
                stream.initialize_playlist(header_sequence, segment_name)
            else:
                # Subsequent init: append new period without truncating playlist
                with open(stream.playlist_file, "a") as f:
                    f.write("#EXT-X-DISCONTINUITY\n")
                    f.write(f"#EXT-X-MAP:URI=\"{segment_name}\"\n")
                stream.period_index += 1
                stream.add_event(f"New init segment (period {stream.period_index}) sequence {header_sequence}")
        # Drop stale media segments from queue (but keep file on disk)
        if (not is_init) and header_sequence <= stream.last_playlist_sequence:
            print(f"Stale segment ignored for playlist: seq={header_sequence} (last={stream.last_playlist_sequence}) stream={stream.stream_id}", flush=True)
            stream.add_event(f"Stale segment ignored: seq={header_sequence}")
        else:
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
                print(f"Starting ffmpeg for stream {stream.stream_id} with {SEGMENTS_BEFORE_RELAY} buffered segments", flush=True)
                stream.start_ffmpeg_relay(header_target, header_stream_key, live_start_index=0)
            elif stream.ffmpeg_process is None or stream.ffmpeg_process.poll() is not None:
                print(f"Restarting ffmpeg for stream {stream.stream_id} at live edge", flush=True)
                if stream.ffmpeg_process and stream.ffmpeg_process.poll() is not None:
                    exit_code = stream.ffmpeg_process.returncode
                    stream.add_event(f"ffmpeg exited with code {exit_code}")
                    stream.last_ffmpeg_exit = {"code": exit_code, "signal": None}
                    stream.ffmpeg_process = None
                    stream._stop_ffmpeg_logger()
                stream.start_ffmpeg_relay(header_target, header_stream_key, live_start_index=None)

        stream.record_upload_duration(time.perf_counter() - request_start)

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


@app.route("/status/<stream_key>")
def stream_status(stream_key):
    now = time.time()
    with stream_creation_lock:
        stream = streams.get(stream_key)

    if stream is None:
        status = {
            "stream_key": stream_key,
            "active": False,
            "recent_stream_dirs": []
        }
        try:
            for name in sorted(os.listdir(BASE_SEGMENTS_DIR), reverse=True):
                if name.startswith(f"{stream_key}_"):
                    status["recent_stream_dirs"].append(name)
                if len(status["recent_stream_dirs"]) >= 5:
                    break
        except FileNotFoundError:
            status["recent_stream_dirs"] = []
        return jsonify(status)

    with stream.playlist_lock:
        pending_sequences = sorted(seq for seq in stream.arrived_segments.keys() if isinstance(seq, int))
        has_finalize_flag = 'final' in stream.arrived_segments
        upload_window_start = now - UPLOAD_UTIL_WINDOW
        upload_active_seconds = sum(duration for ts, duration in stream.upload_history if ts >= upload_window_start)
        last_seq = stream.last_playlist_sequence
        info = {
            "stream_key": stream.stream_key,
            "stream_id": stream.stream_id,
            "active": not stream.finalized,
            "period_index": stream.period_index,
            "map_written": stream.map_written,
            "written_media_segments": stream.written_segment_count,
            "last_playlist_sequence": last_seq,
            "pending_sequences": pending_sequences,
            "pending_count": len(pending_sequences),
            "has_finalize_flag": has_finalize_flag,
            "gap_wait_sequence": stream._gap_wait_seq,
            "gap_wait_elapsed": None if stream._gap_wait_start is None else max(0.0, now - stream._gap_wait_start),
            "upload_window_seconds": UPLOAD_UTIL_WINDOW,
            "upload_active_seconds": upload_active_seconds,
            "upload_utilization": min(1.0, upload_active_seconds / UPLOAD_UTIL_WINDOW) if UPLOAD_UTIL_WINDOW else None,
            "upload_samples": len(stream.upload_history),
            "events": list(stream.events),
            "last_ffmpeg_exit": stream.last_ffmpeg_exit
        }

    info.update({
        "last_upload_age": max(0.0, now - stream.last_upload_time),
        "last_playlist_update_age": max(0.0, now - stream.last_add_time),
        "ffmpeg_running": stream.ffmpeg_process is not None and stream.ffmpeg_process.poll() is None,
        "segments_dir": stream.stream_dir,
    })

    return jsonify(info)

if __name__ == "__main__":
    from waitress import serve
    print(f"Starting production server with Waitress on http://0.0.0.0:{PORT}", flush=True)
    serve(app, host="0.0.0.0", port=PORT)
