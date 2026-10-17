#!/usr/bin/env python3
"""Focused regression tests for the 3D mesh lane selection in server.py.

Covers the 62b7e44dea15 failure: with no local tripoSR_src installed, a cloud
failure must surface re-upload guidance — never a raw server path (ENOENT).

Zero spend: tripo_cloud is stubbed in sys.modules, no network is touched.
Run:  python3 site/test_pipeline.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


class StubTripoCloud:
    """Zero-spend stand-in for tripo_cloud.build_mesh."""
    calls = []
    fail_with = None

    @staticmethod
    def build_mesh(input_jpg, dst_glb, status_cb=None):
        StubTripoCloud.calls.append((input_jpg, dst_glb))
        if StubTripoCloud.fail_with is not None:
            raise StubTripoCloud.fail_with
        if status_cb:
            status_cb("stubbed")
        with open(dst_glb, "wb") as f:
            f.write(b"GLB-STUB")
        return dst_glb


class BuildMeshTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rf-mesh-")
        with open(os.path.join(self.tmp, "input.jpg"), "wb") as f:
            f.write(b"JPEG-STUB")
        self._real_tripo = sys.modules.get("tripo_cloud")
        sys.modules["tripo_cloud"] = StubTripoCloud
        StubTripoCloud.calls = []
        StubTripoCloud.fail_with = None
        self._real_key = server.TRIPO_KEY
        server.TRIPO_KEY = "test-key-zero-spend"
        self._real_src = server.TRIPOSR_SRC

    def tearDown(self):
        if self._real_tripo is None:
            sys.modules.pop("tripo_cloud", None)
        else:
            sys.modules["tripo_cloud"] = self._real_tripo
        server.TRIPO_KEY = self._real_key
        server.TRIPOSR_SRC = self._real_src

    def test_cloud_success_writes_mesh(self):
        out = server.build_mesh(self.tmp, "testjob1")
        self.assertTrue(os.path.exists(out))
        self.assertEqual(len(StubTripoCloud.calls), 1)

    def test_cloud_failure_without_fallback_gives_guidance(self):
        StubTripoCloud.fail_with = RuntimeError("API overloaded")
        server.TRIPOSR_SRC = os.path.join(self.tmp, "does-not-exist")
        with self.assertRaises(RuntimeError) as cm:
            server.build_mesh(self.tmp, "testjob2")
        msg = str(cm.exception)
        self.assertIn("re-upload", msg)
        self.assertNotIn("tripoSR_src", msg)
        self.assertNotIn("Errno", msg)

    def test_missing_key_gives_config_guidance(self):
        server.TRIPO_KEY = ""
        server.TRIPOSR_SRC = os.path.join(self.tmp, "does-not-exist")
        with self.assertRaises(RuntimeError) as cm:
            server.build_mesh(self.tmp, "testjob3")
        self.assertIn("TRIPO_API_KEY", str(cm.exception))


if __name__ == "__main__":
    unittest.main(verbosity=1)
