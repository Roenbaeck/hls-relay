# HLS-relay
This is a very simple HTTP server set up to accept an HLS stream in fMP4 (fragmented MP4) format and relaying it to YouTube as HLS remuxed to M2TS without re-encoding. It's intended to use with the Tubeist iPhone app: https://github.com/Roenbaeck/tubeist.

# Usage
You will need Python installed with the Flask module. I use this on Alpine Linux where `apk add py3-flask` installed the dependency. I am sure it can be done with pip in a virtual environment as well, but setting that up goes beyond my Python knowledge. Additionally you will need ffmpeg installed, since it manages the remuxing and relaying to YouTube. Version 7.x or higher of ffmpeg is recommended. If you use version 6.x of ffmpeg you will have to remove the `reconnect_delay_total_max` option. 

In order for the relay to work you will need a HLS Stream Key from YouTube. In YouTube Studio, create a new stream key and select HLS as the ingest method. This key is read in a header from the client (Tubeist).