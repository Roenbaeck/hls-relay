# HLS-relay
This is a very simple HTTP server set up to accept an HLS stream in fMP4 (fragmented MP4) format and relaying it to YouTube as HLS remuxed to M2TS without re-encoding.

# Usage
You will need Python installed with the Flask module. I use this on Alpine Linux where `apk add py3-flask` installed the dependency. I am sure it can be done with pip in a virtual environment as well, but setting that up goes beyond my Python knowledge. Additionally you will need ffmpeg installed, since it manages the remuxing and relaying to YouTube. The version I have used for testing is 6.1.1.

In order for the relay to work you will need to provide your Stream Key from YouTube. In YouTube Studio, create a new stream key and select HLS as the ingest method. Then set the `STREAM_KEY` variable in the `hls_relay.py` file.
