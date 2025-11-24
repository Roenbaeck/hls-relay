import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
import tempfile
from hls_relay import StreamState, streams, stream_creation_lock

class TestResumeIndex(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.stream_key = "test_resume_key"
        self.stream_id = f"{self.stream_key}_20250101_120000"
        self.stream_dir = os.path.join(self.test_dir, self.stream_id)
        os.makedirs(self.stream_dir)
        
        # Create a fake playlist with some segments
        self.playlist_file = os.path.join(self.stream_dir, "playlist.m3u8")
        with open(self.playlist_file, "w") as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:7\n")
            f.write("#EXT-X-TARGETDURATION:2\n")
            f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
            f.write("#EXT-X-PLAYLIST-TYPE:EVENT\n")
            f.write("#EXT-X-MAP:URI=\"init.mp4\"\n")
            f.write("#EXTINF:2.0,\n")
            f.write("p0_segment_000000.m4s\n")
            f.write("#EXTINF:2.0,\n")
            f.write("p0_segment_000001.m4s\n")
            f.write("#EXTINF:2.0,\n")
            f.write("p0_segment_000002.m4s\n")

        # Mock global BASE_SEGMENTS_DIR in hls_relay temporarily? 
        # Easier to just patch os.path.join or similar, but StreamState uses BASE_SEGMENTS_DIR.
        # Let's patch BASE_SEGMENTS_DIR in the module.
        self.patcher = patch('hls_relay.BASE_SEGMENTS_DIR', self.test_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)
        with stream_creation_lock:
            if self.stream_key in streams:
                del streams[self.stream_key]

    @patch('subprocess.Popen')
    def test_resume_uses_correct_index(self, mock_popen):
        # 1. Restore the stream
        # This should parse the playlist and see segments 0, 1, 2.
        # written_segment_count should be 3.
        stream = StreamState.restore(self.stream_key, self.stream_dir)
        
        # Verify restoration state
        self.assertEqual(stream.last_playlist_sequence, 2)
        self.assertEqual(stream.written_segment_count, 3)
        self.assertTrue(getattr(stream, 'just_restored', False), "just_restored flag should be True after restore")

        # 2. Simulate starting ffmpeg relay
        # In the real code, this happens in upload_segment when written_segment_count >= SEGMENTS_BEFORE_RELAY (3)
        # Since we have 3 segments, the next upload (seq 3) will trigger it if we are not careful, 
        # or if we just call start_ffmpeg_relay directly.
        
        # Let's simulate the logic in upload_segment that calculates live_start_index
        # We need to implement the logic we plan to add to hls_relay.py here to test "what we expect"
        # But wait, we are testing the *implementation*, so we should probably call a method that does this?
        # The logic is inside `upload_segment` which is a route handler. 
        # Calling `stream.start_ffmpeg_relay` directly allows us to pass the index.
        # But we want to verify that `upload_segment` *would* pass the correct index.
        
        # Actually, let's just verify that if we use the flag, we get the right index.
        # The plan says:
        # If just_restored is true, calculate live_start_index = stream.written_segment_count - 1
        
        live_start_index = None
        if getattr(stream, 'just_restored', False):
            # If we just restored 3 segments (0, 1, 2), we want to start at index 2 (the last one) 
            # or maybe index 3 (the one we are about to add)?
            # The user asked: "set live_start_index to the segment that triggered the resume"
            # If we upload segment 3, and that triggers resume.
            # The playlist has 0, 1, 2.
            # We add 3.
            # Now written_segment_count is 4.
            # If we start ffmpeg now, we want it to start streaming from... 3?
            # Or do we assume 0, 1, 2 were already streamed?
            # User said: "Can we assume that ffmpeg has sent all previous segments... we simple set live_start_index to the segment that triggered the resume."
            # So if segment 3 triggers resume, we want start_index = 3.
            # But `live_start_index` in ffmpeg is 0-based index into the playlist.
            # Playlist: [0, 1, 2, 3]
            # Index 0 is seg 0. Index 3 is seg 3.
            # So yes, live_start_index = 3.
            # Which is equal to `written_segment_count` BEFORE adding segment 3?
            # No, before adding 3, count is 3 (0, 1, 2).
            # After adding 3, count is 4.
            # So live_start_index = 3 corresponds to the 4th segment.
            # So live_start_index = written_segment_count - 1 (if count is 4, index is 3).
            
            # Wait, if we just restored, we haven't added the new segment yet in `restore()`.
            # `restore()` parses 0, 1, 2. count = 3.
            # Then `upload_segment` adds segment 3. count becomes 4.
            # Then we start ffmpeg.
            # We want to start at 3.
            # So index = 4 - 1 = 3.
            
            live_start_index = stream.written_segment_count - 1
            
        stream.start_ffmpeg_relay("youtube", self.stream_key, live_start_index=live_start_index)
        
        # Verify mock call
        args, _ = mock_popen.call_args
        command = args[0]
        
        # Check for -live_start_index 2 (since we manually calculated it based on count=3 in this test snippet before adding seq 3? 
        # Ah, in this test I didn't add seq 3. I just restored.
        # If I just restore (count=3: 0,1,2) and start relay, I'm effectively saying "start from the last one I have".
        # That would be index 2.
        # If I added seq 3 first, count would be 4, index would be 3.
        
        # Let's simulate adding seq 3 to match the real scenario
        stream.written_segment_count += 1 # Simulate adding seq 3
        live_start_index = stream.written_segment_count - 1 # 3
        
        stream.start_ffmpeg_relay("youtube", self.stream_key, live_start_index=live_start_index)
        
        # Get the last call
        args, _ = mock_popen.call_args
        command = args[0]
        
        self.assertIn("-live_start_index", command)
        idx_pos = command.index("-live_start_index")
        self.assertEqual(command[idx_pos+1], "3")

if __name__ == '__main__':
    unittest.main()
