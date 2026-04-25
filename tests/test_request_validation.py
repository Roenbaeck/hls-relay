import os
import shutil
import tempfile
import unittest
from base64 import b64encode
from unittest.mock import patch

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

    def upload(self, stream_key, segment_type, sequence, duration, data=b'data'):
        return self.client.post(
            '/upload_segment',
            headers={
                **self.auth_headers,
                'Target': 'passive',
                'Stream-Key': stream_key,
                'Segment-Type': segment_type,
                'Discontinuity': 'false',
                'Duration': str(duration),
                'Sequence': str(sequence),
            },
            data=data,
            environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
        )

    def test_invalid_stream_key_is_rejected(self):
        response = self.upload('../../bad key', 'Initialization', 0, 0, data=b'init')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_data(as_text=True), 'Invalid Stream-Key')

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


if __name__ == '__main__':
    unittest.main()