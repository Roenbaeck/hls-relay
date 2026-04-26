import os
import shutil
import tempfile
import unittest
from base64 import b64encode
from unittest.mock import MagicMock, patch

import hls_relay


class TestRequestValidation(unittest.TestCase):
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

    def upload(self, stream_key, segment_type, sequence, duration, data=b'data', stream_id=None):
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

        return self.client.post(
            '/upload_segment',
            headers=headers,
            data=data,
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )

    def upload_with_target(self, target, stream_key, segment_type, sequence, duration, data=b'data', stream_id=None):
        headers = {
            **self.auth_headers,
            'Target': target,
            'Stream-Key': stream_key,
            'Segment-Type': segment_type,
            'Discontinuity': 'false',
            'Duration': str(duration),
            'Sequence': str(sequence),
        }
        if stream_id is not None:
            headers['Stream-ID'] = stream_id

        return self.client.post(
            '/upload_segment',
            headers=headers,
            data=data,
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )

    def test_invalid_stream_key_is_rejected(self):
        response = self.upload('../../bad key', 'Initialization', 0, 0, data=b'init')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Invalid Stream-Key')

    def test_invalid_stream_id_is_rejected(self):
        response = self.upload('valid_key', 'Initialization', 0, 0, data=b'init', stream_id='bad/id')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Invalid Stream-ID')

    def test_zero_duration_finalization_closes_playlist(self):
        self.assertEqual(self.upload('finalize_key', 'Initialization', 0, 0, data=b'init').status_code, 200)
        self.assertEqual(self.upload('finalize_key', 'Media', 1, 2.0, data=b'media').status_code, 200)

        response = self.upload('finalize_key', 'Finalization', 2, 0, data=b'')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), 'Segment uploaded')
        with hls_relay.stream_creation_lock:
            self.assertNotIn('finalize_key', hls_relay.streams)

        stream_dirs = os.listdir(self.test_dir)
        self.assertEqual(len(stream_dirs), 1)
        playlist_path = os.path.join(self.test_dir, stream_dirs[0], 'playlist.m3u8')
        with open(playlist_path, 'r') as f:
            playlist = f.read()

        self.assertIn('#EXT-X-ENDLIST', playlist)

    def test_serving_endpoints_reject_invalid_path_components(self):
        response = self.client.get(
            '/segments/bad..stream/playlist.m3u8',
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Invalid stream ID')

        segment_dir = os.path.join(self.test_dir, 'valid_stream_20250101_120000')
        os.makedirs(segment_dir)
        with open(os.path.join(segment_dir, 'p0_segment_000001.m4s'), 'wb') as f:
            f.write(b'segment')

        response = self.client.get(
            '/segments/valid_stream_20250101_120000/bad..segment.m4s',
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Invalid segment name')

    def test_old_client_does_not_resume_without_stream_id(self):
        self.assertEqual(self.upload('legacy_key', 'Initialization', 0, 0, data=b'init').status_code, 200)
        self.assertEqual(self.upload('legacy_key', 'Media', 1, 2.0, data=b'media').status_code, 200)
        self.assertEqual(self.upload('legacy_key', 'Finalization', 2, 0, data=b'').status_code, 200)

        response = self.upload('legacy_key', 'Media', 3, 2.0, data=b'late')

        self.assertEqual(response.status_code, 200)
        stream_dirs = sorted(os.listdir(self.test_dir))
        self.assertEqual(len(stream_dirs), 2)
        self.assertNotEqual(stream_dirs[0], stream_dirs[1])

        with hls_relay.stream_creation_lock:
            stream = hls_relay.streams.get('legacy_key')
            self.assertIsNotNone(stream)
            self.assertEqual(stream.last_playlist_sequence, -1)
            self.assertFalse(stream.just_restored)

    def test_stream_id_resumes_exact_matching_stream(self):
        stream_id = '20260425_150000'
        self.assertEqual(self.upload('resume_key', 'Initialization', 0, 0, data=b'init', stream_id=stream_id).status_code, 200)
        self.assertEqual(self.upload('resume_key', 'Media', 1, 2.0, data=b'media', stream_id=stream_id).status_code, 200)
        self.assertEqual(self.upload('resume_key', 'Finalization', 2, 0, data=b'', stream_id=stream_id).status_code, 200)

        response = self.upload('resume_key', 'Media', 3, 2.0, data=b'late', stream_id=stream_id)

        self.assertEqual(response.status_code, 200)
        stream_dirs = os.listdir(self.test_dir)
        self.assertEqual(stream_dirs, [f'resume_key_{stream_id}'])

        with hls_relay.stream_creation_lock:
            stream = hls_relay.streams.get('resume_key')
            self.assertIsNotNone(stream)
            self.assertEqual(stream.stream_id, f'resume_key_{stream_id}')
            self.assertTrue(stream.just_restored)

    def test_finalization_does_not_restart_ffmpeg(self):
        with patch.object(hls_relay.StreamState, 'start_ffmpeg_relay') as mock_start:
            self.assertEqual(self.upload_with_target('youtube', 'ffmpeg_final_key', 'Initialization', 0, 0, data=b'init').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'ffmpeg_final_key', 'Media', 1, 2.0, data=b'media1').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'ffmpeg_final_key', 'Media', 2, 2.0, data=b'media2').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'ffmpeg_final_key', 'Media', 3, 2.0, data=b'media3').status_code, 200)

            self.assertEqual(mock_start.call_count, 1)

            response = self.upload_with_target('youtube', 'ffmpeg_final_key', 'Finalization', 4, 0, data=b'')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_start.call_count, 1)

    def test_finalization_prefers_drain_over_immediate_stop(self):
        with patch.object(hls_relay.StreamState, 'start_ffmpeg_relay') as mock_start, \
             patch.object(hls_relay.StreamState, '_begin_ffmpeg_drain') as mock_begin_drain, \
             patch.object(hls_relay.StreamState, '_stop_ffmpeg') as mock_stop_ffmpeg:
            self.assertEqual(self.upload_with_target('youtube', 'drain_key', 'Initialization', 0, 0, data=b'init').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'drain_key', 'Media', 1, 2.0, data=b'media1').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'drain_key', 'Media', 2, 2.0, data=b'media2').status_code, 200)
            self.assertEqual(self.upload_with_target('youtube', 'drain_key', 'Media', 3, 2.0, data=b'media3').status_code, 200)
            self.assertEqual(mock_start.call_count, 1)

            with hls_relay.stream_creation_lock:
                stream = hls_relay.streams['drain_key']
                stream.ffmpeg_process = MagicMock()
                stream.ffmpeg_process.poll.return_value = None

            response = self.upload_with_target('youtube', 'drain_key', 'Finalization', 4, 0, data=b'')

            self.assertEqual(response.status_code, 200)
            mock_begin_drain.assert_called_once()
            mock_stop_ffmpeg.assert_not_called()

    def test_replacement_stops_old_ffmpeg_immediately(self):
        with patch.object(hls_relay.StreamState, '_begin_ffmpeg_drain') as mock_begin_drain, \
             patch.object(hls_relay.StreamState, '_stop_ffmpeg') as mock_stop_ffmpeg:
            self.assertEqual(self.upload_with_target('youtube', 'replace_key', 'Initialization', 0, 0, data=b'init', stream_id='session_a').status_code, 200)

            with hls_relay.stream_creation_lock:
                old_stream = hls_relay.streams['replace_key']
                old_stream.ffmpeg_process = MagicMock()
                old_stream.ffmpeg_process.poll.return_value = None

            response = self.upload_with_target('youtube', 'replace_key', 'Initialization', 0, 0, data=b'new_init', stream_id='session_b')

            self.assertEqual(response.status_code, 200)
            mock_stop_ffmpeg.assert_called_once()
            self.assertFalse(mock_begin_drain.called)


if __name__ == '__main__':
    unittest.main()