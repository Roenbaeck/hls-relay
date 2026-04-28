import os
import shutil
import tempfile
import threading
import time
import unittest
from base64 import b64encode
from unittest.mock import MagicMock, patch

import hls_relay


class TestPlaylistBehavior(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.base_dir_patcher = patch('hls_relay.BASE_SEGMENTS_DIR', self.test_dir)
        self.base_dir_patcher.start()
        os.makedirs(hls_relay.BASE_SEGMENTS_DIR, exist_ok=True)
        self.client = hls_relay.app.test_client()
        token = b64encode(b'brute:force').decode()
        self.auth_headers = {"Authorization": f"Basic {token}"}

    def tearDown(self):
        self.base_dir_patcher.stop()
        with hls_relay.stream_creation_lock:
            hls_relay.streams.clear()
        shutil.rmtree(self.test_dir)

    def upload(self, stream_key, segment_type, sequence, duration, data=b'data', stream_id=None, remote_addr='127.0.0.1', extra_headers=None):
        headers = {
            **self.auth_headers,
            'Target': 'passive',
            'Stream-Key': stream_key,
            'Segment-Type': segment_type,
            'Discontinuity': 'false',
            'Duration': str(duration),
            'Sequence': str(sequence),
        }
        if stream_id is not None:
            headers['Stream-ID'] = stream_id
        if extra_headers:
            headers.update(extra_headers)

        return self.client.post(
            '/upload_segment',
            headers=headers,
            data=data,
            environ_overrides={'REMOTE_ADDR': remote_addr},
        )

    def write_playlist(self, stream_dir_name, lines):
        stream_dir = os.path.join(self.test_dir, stream_dir_name)
        os.makedirs(stream_dir, exist_ok=True)
        playlist_file = os.path.join(stream_dir, 'playlist.m3u8')
        with open(playlist_file, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        return stream_dir, playlist_file

    def test_finalize_waits_for_inflight_playlist_update(self):
        stream = hls_relay.StreamState('race_key')
        stream.initialize_playlist(0, 'p0_segment_000000.mp4')
        stream.last_playlist_sequence = 0
        stream.arrived_segments[1] = {
            'filename': 'p0_segment_000001.m4s',
            'duration': 2.0,
            'is_init': False,
            'discontinuity': False,
        }

        started = threading.Event()

        def finalize_in_background():
            started.set()
            stream.finalize_playlist(stop_ffmpeg_immediately=True)

        with stream.playlist_lock:
            worker = threading.Thread(target=finalize_in_background)
            worker.start()
            self.assertTrue(started.wait(timeout=1))
            stream.update_playlist()
            self.assertFalse(stream.finalized)

        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())

        with open(stream.playlist_file, 'r') as f:
            playlist_lines = f.read().splitlines()

        self.assertIn('p0_segment_000001.m4s', playlist_lines)
        self.assertEqual(playlist_lines[-1], '#EXT-X-ENDLIST')
        self.assertLess(playlist_lines.index('p0_segment_000001.m4s'), playlist_lines.index('#EXT-X-ENDLIST'))

    def test_gap_skip_after_timeout_writes_discontinuity(self):
        stream = hls_relay.StreamState('gap_skip_key')
        stream.initialize_playlist(0, 'p0_segment_000000.mp4')
        with open(stream.playlist_file, 'a') as f:
            f.write('#EXTINF:2.000000,\n')
            f.write('p0_segment_000001.m4s\n')
        stream.last_playlist_sequence = 1
        stream.written_segment_count = 1
        stream._gap_wait_seq = 2
        stream._gap_wait_start = time.time() - hls_relay.GAP_SKIP_TIMEOUT - 1
        stream.arrived_segments[3] = {
            'filename': 'p0_segment_000003.m4s',
            'duration': 2.0,
            'is_init': False,
            'discontinuity': False,
        }

        stream.update_playlist()

        with open(stream.playlist_file, 'r') as f:
            playlist = f.read()

        self.assertIn('#EXT-X-DISCONTINUITY', playlist)
        self.assertIn('p0_segment_000003.m4s', playlist)
        self.assertEqual(stream.last_playlist_sequence, 3)

    def test_gap_skip_waits_before_timeout(self):
        stream = hls_relay.StreamState('gap_wait_key')
        stream.initialize_playlist(0, 'p0_segment_000000.mp4')
        with open(stream.playlist_file, 'a') as f:
            f.write('#EXTINF:2.000000,\n')
            f.write('p0_segment_000001.m4s\n')
        stream.last_playlist_sequence = 1
        stream.written_segment_count = 1
        stream._gap_wait_seq = 2
        stream._gap_wait_start = time.time()
        stream.arrived_segments[3] = {
            'filename': 'p0_segment_000003.m4s',
            'duration': 2.0,
            'is_init': False,
            'discontinuity': False,
        }

        stream.update_playlist()

        with open(stream.playlist_file, 'r') as f:
            playlist = f.read()

        self.assertNotIn('p0_segment_000003.m4s', playlist)
        self.assertIn(3, stream.arrived_segments)
        self.assertEqual(stream.last_playlist_sequence, 1)

    def test_restore_multi_period_playlist_reconstructs_state(self):
        stream_dir, _ = self.write_playlist(
            'restore_key_20260428_120000',
            [
                '#EXTM3U',
                '#EXT-X-VERSION:7',
                '#EXT-X-TARGETDURATION:2',
                '#EXT-X-MEDIA-SEQUENCE:0',
                '#EXT-X-PLAYLIST-TYPE:EVENT',
                '#EXT-X-MAP:URI="p0_segment_000000.mp4"',
                '#EXTINF:2.000000,',
                'p0_segment_000001.m4s',
                '#EXT-X-DISCONTINUITY',
                '#EXT-X-MAP:URI="p1_segment_000000.mp4"',
                '#EXTINF:2.000000,',
                'p1_segment_000002.m4s',
            ],
        )

        stream = hls_relay.StreamState.restore('restore_key', stream_dir)

        self.assertEqual(stream.period_index, 1)
        self.assertEqual(stream.written_segment_count, 2)
        self.assertEqual(stream.last_playlist_sequence, 2)
        self.assertTrue(stream.just_restored)

    def test_restore_removes_stale_endlist(self):
        stream_dir, playlist_file = self.write_playlist(
            'endlist_key_20260428_120001',
            [
                '#EXTM3U',
                '#EXT-X-VERSION:7',
                '#EXT-X-TARGETDURATION:2',
                '#EXT-X-MEDIA-SEQUENCE:0',
                '#EXT-X-PLAYLIST-TYPE:EVENT',
                '#EXT-X-MAP:URI="p0_segment_000000.mp4"',
                '#EXTINF:2.000000,',
                'p0_segment_000001.m4s',
                '#EXT-X-ENDLIST',
            ],
        )

        stream = hls_relay.StreamState.restore('endlist_key', stream_dir)

        with open(playlist_file, 'r') as f:
            playlist = f.read()

        self.assertNotIn('#EXT-X-ENDLIST', playlist)
        self.assertTrue(any('Removed #EXT-X-ENDLIST' in event['message'] for event in stream.events))

    def test_playlist_endpoint_requires_localhost(self):
        stream_dir, _ = self.write_playlist(
            'serve_key_20260428_120002',
            ['#EXTM3U'],
        )

        response = self.client.get(
            f"/segments/{os.path.basename(stream_dir)}/playlist.m3u8",
            environ_overrides={'REMOTE_ADDR': '10.0.0.5'},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_data(as_text=True), 'Access denied')

    def test_segment_endpoint_requires_localhost(self):
        stream_dir = os.path.join(self.test_dir, 'segment_key_20260428_120003')
        os.makedirs(stream_dir, exist_ok=True)
        segment_path = os.path.join(stream_dir, 'p0_segment_000001.m4s')
        with open(segment_path, 'wb') as f:
            f.write(b'segment')

        response = self.client.get(
            f"/segments/{os.path.basename(stream_dir)}/p0_segment_000001.m4s",
            environ_overrides={'REMOTE_ADDR': '10.0.0.5'},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_data(as_text=True), 'Access denied')

    def test_missing_required_header_returns_400(self):
        headers = {
            **self.auth_headers,
            'Target': 'passive',
            'Stream-Key': 'missing_header_key',
            'Segment-Type': 'Media',
            'Discontinuity': 'false',
            'Sequence': '1',
        }

        response = self.client.post(
            '/upload_segment',
            headers=headers,
            data=b'media',
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Missing headers: Duration')

    def test_invalid_duration_header_returns_400(self):
        response = self.upload('bad_duration_key', 'Media', 1, 'not-a-number')

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid header data', response.get_data(as_text=True))

    def test_invalid_sequence_header_returns_400(self):
        headers = {
            **self.auth_headers,
            'Target': 'passive',
            'Stream-Key': 'bad_sequence_key',
            'Segment-Type': 'Media',
            'Discontinuity': 'false',
            'Duration': '2.0',
            'Sequence': 'not-an-int',
        }

        response = self.client.post(
            '/upload_segment',
            headers=headers,
            data=b'media',
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid header data', response.get_data(as_text=True))

    def test_segment_save_failure_returns_500(self):
        original_open = open

        def failing_open(path, mode='r', *args, **kwargs):
            if isinstance(path, str) and path.endswith('p0_segment_000000.mp4') and 'save_fail_key' in path and 'w' in mode:
                raise OSError('disk full')
            return original_open(path, mode, *args, **kwargs)

        with patch('builtins.open', side_effect=failing_open):
            response = self.upload('save_fail_key', 'Initialization', 0, 0, data=b'init')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_data(as_text=True), 'Error saving segment: disk full')

    def test_finalization_segment_is_written_and_closes_playlist(self):
        self.assertEqual(self.upload('final_only_key', 'Initialization', 0, 0, data=b'init').status_code, 200)

        response = self.upload('final_only_key', 'Finalization', 1, 0, data=b'')

        self.assertEqual(response.status_code, 200)
        stream_dir = os.path.join(self.test_dir, os.listdir(self.test_dir)[0])
        playlist_file = os.path.join(stream_dir, 'playlist.m3u8')
        with open(playlist_file, 'r') as f:
            playlist = f.read()

        self.assertIn('#EXTINF:0.000000,', playlist)
        self.assertIn('p0_segment_000001.m4s', playlist)
        self.assertTrue(os.path.exists(os.path.join(stream_dir, 'p0_segment_000001.m4s')))
        self.assertTrue(playlist.rstrip().endswith('#EXT-X-ENDLIST'))

    def test_ffmpeg_restart_backoff_records_suppression_event(self):
        with patch.object(hls_relay.StreamState, 'start_ffmpeg_relay') as mock_start:
            self.assertEqual(self.upload('backoff_event_key', 'Initialization', 0, 0, data=b'init', extra_headers={'Target': 'youtube'}).status_code, 200)
            self.assertEqual(self.upload('backoff_event_key', 'Media', 1, 2.0, data=b'media1', extra_headers={'Target': 'youtube'}).status_code, 200)
            self.assertEqual(self.upload('backoff_event_key', 'Media', 2, 2.0, data=b'media2', extra_headers={'Target': 'youtube'}).status_code, 200)
            self.assertEqual(self.upload('backoff_event_key', 'Media', 3, 2.0, data=b'media3', extra_headers={'Target': 'youtube'}).status_code, 200)
            self.assertEqual(mock_start.call_count, 1)

            with hls_relay.stream_creation_lock:
                stream = hls_relay.streams['backoff_event_key']
                stream.ffmpeg_process = MagicMock()
                stream.ffmpeg_process.poll.return_value = 1
                stream.ffmpeg_process.returncode = 1

            response = self.upload('backoff_event_key', 'Media', 4, 2.0, data=b'media4', extra_headers={'Target': 'youtube'})

        self.assertEqual(response.status_code, 200)
        with hls_relay.stream_creation_lock:
            stream = hls_relay.streams['backoff_event_key']
            self.assertTrue(any('restart suppressed' in event['message'] for event in stream.events))


if __name__ == '__main__':
    unittest.main()