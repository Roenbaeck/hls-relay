There is a bug causing a restart of ffmpeg after finalization. See log: 

Saved segment: p0_segment_000035.m4s for stream: rupg-prqt-bk24-4rck-07ve_20260426_163710
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:02.36 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:02.85 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:03.36 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:03.85 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f10ca4f8600] Skip ('#EXT-X-VERSION:7')
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f10ca4f8600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000000.mp4' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f10ca4f8600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000034.m4s' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [mov,mp4,m4a,3gp,3g2,mj2 @ 0x7f10c9f1d100] Found duplicated MOOV Atom. Skipped it
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [mov,mp4,m4a,3gp,3g2,mj2 @ 0x7f10c9f1d100] Duplicated SBGP sync atom
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f10c13c1b80] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master31.ts' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f10c13c1b80] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master.m3u8' for writing
Saved segment: p0_segment_000036.m4s for stream: rupg-prqt-bk24-4rck-07ve_20260426_163710
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:04.36 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:04.85 bitrate=N/A speed=1.01x
Finalization segment received: stream_key=rupg-prqt-bk24-4rck-07ve sequence=37
Saved segment: p0_segment_000037.m4s for stream: rupg-prqt-bk24-4rck-07ve_20260426_163710
Finalization segment processed: stream=rupg-prqt-bk24-4rck-07ve_20260426_163710 sequence=37 action=finalize_requested
Finalizing playlist for stream rupg-prqt-bk24-4rck-07ve_20260426_163710
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:05.36 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f10c13c1b80] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master32.ts' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f10c13c1b80] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master.m3u8' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [out#0/hls @ 0x7f10c717cec0] video:25080kB audio:526kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:01:05.36 bitrate=N/A speed=1.01x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] Exiting normally, received signal 15.
Restarting ffmpeg for stream rupg-prqt-bk24-4rck-07ve_20260426_163710 at live edge (target=youtube)
Starting ffmpeg relay for stream rupg-prqt-bk24-4rck-07ve to target youtube with live_start_index edge
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] ffmpeg version 6.1.2 Copyright (c) 2000-2024 the FFmpeg developers
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   built with gcc 14.2.0 (Alpine 14.2.0)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   configuration: --prefix=/usr --disable-librtmp --disable-lzma --disable-static --disable-stripping --enable-avfilter --enable-gpl --enable-ladspa --enable-libaom --enable-libass --enable-libbluray --enable-libdav1d --enable-libdrm --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libharfbuzz --enable-libmp3lame --enable-libopenmpt --enable-libopus --enable-libplacebo --enable-libpulse --enable-librav1e --enable-librist --enable-libsoxr --enable-libsrt --enable-libssh --enable-libtheora --enable-libv4l2 --enable-libvidstab --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxcb --enable-libxml2 --enable-libxvid --enable-libzimg --enable-libzmq --enable-lto=auto --enable-lv2 --enable-openssl --enable-pic --enable-postproc --enable-pthreads --enable-shared --enable-vaapi --enable-vdpau --enable-version3 --enable-vulkan --optflags=-O3 --enable-libjxl --enable-libsvtav1 --enable-libvpl
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libavutil      58. 29.100 / 58. 29.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libavcodec     60. 31.102 / 60. 31.102
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libavformat    60. 16.100 / 60. 16.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libavdevice    60.  3.100 / 60.  3.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libavfilter     9. 12.100 /  9. 12.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libswscale      7.  5.100 /  7.  5.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libswresample   4. 12.100 /  4. 12.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   libpostproc    57.  3.100 / 57.  3.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Skip ('#EXT-X-VERSION:7')
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000000.mp4' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000001.m4s' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000002.m4s' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] DTS 80 < 120 out of order
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] Input #0, hls, from 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/playlist.m3u8':
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Duration: 00:01:12.87, start: 0.066667, bitrate: N/A
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Program 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       variant_bitrate : 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:0(und): Video: hevc (Main 10) (hvc1 / 0x31637668), yuv420p10le(tv, bt2020nc/bt2020/arib-std-b67), 1280x720, 3207 kb/s, 600 fps, 30 tbr, 600 tbn (default)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       variant_bitrate : 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       compatible_brands: isomiso5hlsf
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       handler_name    : Core Media Video
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       vendor_id       : [0][0][0][0]
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       major_brand     : iso5
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       minor_version   : 1
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       creation_time   : 2026-04-26T14:37:10.000000Z
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Side data:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       DOVI configuration record: version: 1.0, profile: 8, level: 2, rpu flag: 1, el flag: 0, bl flag: 1, compatibility id: 4
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:1(und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 50 kb/s (default)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       variant_bitrate : 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       creation_time   : 2026-04-26T14:37:17.000000Z
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       handler_name    : Core Media Audio
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       vendor_id       : [0][0][0][0]
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] Output #0, hls, to 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master.m3u8':
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     encoder         : Lavf60.16.100
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:0(und): Video: hevc (Main 10) (hvc1 / 0x31637668), yuv420p10le(tv, bt2020nc/bt2020/arib-std-b67), 1280x720, q=2-31, 3207 kb/s, 600 fps, 30 tbr, 90k tbn (default)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       variant_bitrate : 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       compatible_brands: isomiso5hlsf
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       handler_name    : Core Media Video
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       vendor_id       : [0][0][0][0]
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       major_brand     : iso5
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       minor_version   : 1
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       creation_time   : 2026-04-26T14:37:10.000000Z
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Side data:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       DOVI configuration record: version: 1.0, profile: 8, level: 2, rpu flag: 1, el flag: 0, bl flag: 1, compatibility id: 4
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:1(und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 50 kb/s (default)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]     Metadata:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       variant_bitrate : 0
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       creation_time   : 2026-04-26T14:37:17.000000Z
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       handler_name    : Core Media Audio
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]       vendor_id       : [0][0][0][0]
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] Stream mapping:
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:0 -> #0:0 (copy)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710]   Stream #0:1 -> #0:1 (copy)
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] Press [q] to stop, [?] for help
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=       0kB time=00:00:00.00 bitrate=N/A speed=N/A
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:01.36 bitrate=N/A speed=2.74x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:01.85 bitrate=N/A speed=1.86x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000003.m4s' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [mov,mp4,m4a,3gp,3g2,mj2 @ 0x7f1190f07380] Duplicated SBGP sync atom
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f1190bd0380] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master0.ts' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f118839e0c0] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master.m3u8' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f1190bd0380] Opening 'https://a.upload.youtube.com/master.m3u8' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:02.36 bitrate=N/A speed=1.58x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:02.85 bitrate=N/A speed=1.43x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:03.36 bitrate=N/A speed=1.33x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:03.85 bitrate=N/A speed=1.26x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000004.m4s' for reading
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [mov,mp4,m4a,3gp,3g2,mj2 @ 0x7f1190f07380] Duplicated SBGP sync atom
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f118839e0c0] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master1.ts' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [https @ 0x7f118839e0c0] Opening 'https://a.upload.youtube.com/http_upload_hls?cid=rupg-prqt-bk24-4rck-07ve&copy=0&file=master.m3u8' for writing
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:04.36 bitrate=N/A speed=1.22x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:04.85 bitrate=N/A speed=1.18x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:05.36 bitrate=N/A speed=1.16x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] size=N/A time=00:00:05.85 bitrate=N/A speed=1.13x
[ffmpeg rupg-prqt-bk24-4rck-07ve_20260426_163710] [hls @ 0x7f11914f1600] Opening 'http://127.0.0.1:8080/segments/rupg-prqt-bk24-4rck-07ve_20260426_163710/p0_segment_000005.m4s' for reading

---

I’m checking the relay code around finalization and ffmpeg restart, because your server log already points to a concrete control-flow issue: finalization completes, then the relay immediately starts a new ffmpeg from the beginning of the same playlist.



Fetched https://raw.githubusercontent.com/Roenbaeck/hls-relay/refs/heads/main/hls_relay.py

Yes, this looks like a relay bug, not a client bug.

The important sequence in the relay is:

1. the finalization fragment is uploaded,
2. `stream.update_playlist()` sees the `'final'` flag and calls `finalize_playlist()`,
3. `finalize_playlist()` appends `#EXT-X-ENDLIST`, stops ffmpeg, and marks the stream finalized,
4. then control returns to the same `upload_segment()` request,
5. and the relay-start logic still runs afterward.

That last step is the bug.

In [hls_relay.py](https://raw.githubusercontent.com/Roenbaeck/hls-relay/refs/heads/main/hls_relay.py), the finalization happens inside `update_playlist()`, but the code below it still does this, conceptually:

```python
stream.update_playlist()

if effective_target not in PASSIVE_TARGETS:
    if stream.written_segment_count >= SEGMENTS_BEFORE_RELAY:
        ...
        elif stream.ffmpeg_process is None or stream.ffmpeg_process.poll() is not None:
            print(f"Restarting ffmpeg for stream {stream.stream_id} at live edge")
            stream.start_ffmpeg_relay(...)
```

After finalization, `stream.ffmpeg_process` is `None` because `finalize_playlist()` just stopped it, so this branch fires and ffmpeg is restarted immediately on the finalization request itself.

That matches your server log exactly:

- `Finalization segment processed`
- `Finalizing playlist`
- ffmpeg exits
- `Restarting ffmpeg for stream ...`
- new ffmpeg starts and opens `p0_segment_000000.mp4`, `p0_segment_000001.m4s`, ...

So the relay is reopening the finished playlist after the stream has already been ended. That is the core bug.

There are two concrete problems in that restart:

1. It should not restart at all once `stream.finalized` is true.
2. The restart path uses `live_start_index=None`, which in practice lets ffmpeg begin reading from the start of the playlist again. Your log confirms that by showing it reopening segment 0.

A minimal fix in the relay is to bail out after finalization before any ffmpeg-start logic runs. For example, immediately after `stream.update_playlist()`:

```python
stream.update_playlist()

if stream.finalized:
    stream.record_upload_duration(time.perf_counter() - request_start)
    return "Segment uploaded", 200
```

Or equivalently guard the relay block:

```python
if (not stream.finalized) and effective_target not in PASSIVE_TARGETS:
    ...
```

I would do both defensively, because this is shutdown-sensitive code.

Why this produces the repeated tail on YouTube:

- the first ffmpeg instance already pushed the real stream through the end,
- finalization stops it cleanly,
- then the relay starts a second ffmpeg against the same finished playlist,
- YouTube receives overlapping post-stop uploads from that second session,
- which can show up as repeated tail content rather than a clean end.

So your diagnosis is right: the client log looks clean, and the server log contains the smoking gun.

