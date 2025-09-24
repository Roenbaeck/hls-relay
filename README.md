# HLS-Relay

A simple HTTP server that accepts HLS streams in fragmented MP4 (fMP4) format and relays them to YouTube or Twitch as HLS remuxed to MPEG-TS (M2TS) without re-encoding. Designed for use with live streaming apps like [Tubeist](https://github.com/Roenbaeck/tubeist) for iOS.

## Features

- **Low-Latency Relaying**: Accepts fMP4 HLS segments and forwards them to YouTube/Twitch with minimal processing.
- **No Re-Encoding**: Uses FFmpeg for remuxing only, preserving quality and reducing CPU usage.
- **Multi-Platform Support**: Supports YouTube (HLS upload) and Twitch (RTMP).
- **Automatic Stream Management**: Handles stream initialization, buffering, and finalization.
- **Basic Authentication**: Protects upload endpoints with HTTP Basic Auth.
- **Docker Support**: Easy deployment via Docker (see tutorial below).

## Installation

### Prerequisites
- Python 3.x with Flask (`pip install flask` or `apk add py3-flask` on Alpine Linux)
- FFmpeg 6.x or later (for remuxing and relaying)

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/Roenbaeck/hls-relay.git
   cd hls-relay
   ```

2. Install dependencies:
   ```bash
   pip install flask
   ```

3. Run the server:
   ```bash
   python hls_relay.py
   ```

For Docker setup, see the tutorial: [YouTube Tutorial](https://www.youtube.com/watch?v=Qzq6nCsHt5c)

## Configuration

Edit the constants at the top of `hls_relay.py`:

- `AUTH_USERNAME` / `AUTH_PASSWORD`: Credentials for HTTP Basic Auth (default: `brute` / `force`).
- `PORT`: Server port (default: 8080).
- `SEGMENTS_BEFORE_RELAY`: Number of segments to buffer before starting FFmpeg (default: 3).
- `MISSING_SEGMENT_TIMEOUT`: Timeout in seconds for missing segments (default: 60).

## Usage

### Obtaining Stream Keys
- **YouTube**: In YouTube Studio, create a new live stream and select HLS as the ingest method. Copy the stream key.
- **Twitch**: Get your stream key from the Twitch dashboard.

### Client Integration
This server is designed for use with [Tubeist](https://github.com/Roenbaeck/tubeist), an iOS app available on the [App Store](https://apps.apple.com/us/app/tubeist/id6740208994). Tubeist handles segment uploads automatically for seamless live streaming to YouTube or Twitch.

Alternatively, integrate directly via HTTP requests with the following headers:
- `Target`: `youtube` or `twitch`
- `Stream-Key`: Your platform's stream key
- `Segment-Type`: `Initialization`, `Media`, or `Finalization`
- `Discontinuity`: `true` or `false`
- `Duration`: Segment duration in seconds
- `Sequence`: Segment sequence number

Example with curl:
```bash
curl -X POST http://localhost:8080/upload_segment \
  -u brute:force \
  -H "Target: youtube" \
  -H "Stream-Key: YOUR_YOUTUBE_KEY" \
  -H "Segment-Type: Media" \
  -H "Discontinuity: false" \
  -H "Duration: 2.0" \
  -H "Sequence: 1" \
  --data-binary @segment.m4s
```

## API Endpoints

- `POST /upload_segment`: Upload HLS segments (requires auth).
- `GET /segments/<stream_id>/playlist.m3u8`: Serve the HLS playlist (localhost only).
- `GET /segments/<stream_id>/<segment_name>`: Serve individual segments (localhost only).

## Troubleshooting

- **Streams not appearing on YouTube**: Check FFmpeg logs for errors. Ensure the stream key is correct and the broadcast is started in YouTube Studio.
- **Multiple directories created**: This may indicate gaps in segment uploads. The server finalizes streams after timeouts to prevent stalls.
- **FFmpeg not found**: Install FFmpeg and ensure it's in your PATH.
- **Authentication issues**: Verify the username/password in the request.

For more help, check the logs or open an issue on GitHub.

## Contributing

Contributions are welcome! Please open issues or pull requests.

## License

See [LICENSE.md](LICENSE.md).
