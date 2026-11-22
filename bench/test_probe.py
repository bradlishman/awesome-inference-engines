"""Offline tests for the probe protocol and receipt logic."""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import probe


class FakeServer(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        size = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(size))
        self.server.requests.append(body)
        question = body["messages"][0]["content"]
        answer = "saturn" if "UNIQUE_CHECKWORD:" in question else "cedar"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        chunks = [
            {"choices": [{"delta": {"role": "assistant"}, "index": 0}]},
            {"choices": [{"delta": {"content": answer[:2]}, "index": 0}]},
            {"choices": [{"delta": {"content": answer[2:]}, "index": 0, "finish_reason": "stop"}]},
        ]
        if "stream_options" in body:
            chunks.append({"choices": [], "usage": {"prompt_tokens": 20, "completion_tokens": 2}})
        for chunk in chunks:
            self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode("utf-8"))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeServer)
        cls.server.requests = []
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_loopback_endpoint_and_remote_guard(self):
        self.assertEqual(probe.endpoint_url("http://127.0.0.1:9000/v1", False),
                         "http://127.0.0.1:9000/v1/chat/completions")
        with self.assertRaises(ValueError):
            probe.endpoint_url("https://example.com", False)
        with self.assertRaises(ValueError):
            probe.endpoint_url("http://user:secret@localhost", False)
        self.assertEqual(probe.endpoint_url("https://example.com", True),
                         "https://example.com/v1/chat/completions")

    def test_streaming_usage_and_exact_answer(self):
        case = probe.make_case("short", 8192)
        url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        result = probe.trial(url, "fake-model", case, 32, 10, True, None)
        self.assertTrue(result["exact_answer"])
        self.assertEqual(result["output_chars"], 5)
        self.assertEqual(result["completion_tokens_reported"], 2)
        self.assertIsNotNone(result["ttft_visible_ms"])
        self.assertEqual(result["finish_reason"], "stop")

    def test_without_usage_and_needle_case(self):
        case = probe.make_case("needle", 4096)
        self.assertGreater(len(case["prompt"]), 1024)
        url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        result = probe.trial(url, "fake-model", case, 32, 10, False, None)
        self.assertTrue(result["exact_answer"])
        self.assertIsNone(result["completion_tokens_reported"])
        self.assertIsNone(result["post_first_visible_rate_approx_tok_s"])

    def test_receipt_summary(self):
        samples = [
            {"elapsed_ms": 100, "ttft_visible_ms": 10,
             "post_first_visible_rate_approx_tok_s": None, "exact_answer": True},
            {"elapsed_ms": 200, "ttft_visible_ms": 20,
             "post_first_visible_rate_approx_tok_s": None, "exact_answer": False},
        ]
        summary = probe.summarize(samples)
        self.assertEqual(summary["exact_answers"], 1)
        self.assertEqual(summary["elapsed_ms"]["median"], 150)
        self.assertIsNone(summary["post_first_visible_rate_approx_tok_s"])

    def test_full_receipt_and_no_endpoint_or_key_in_output(self):
        args = probe.build_parser().parse_args([
            "--base-url", f"http://127.0.0.1:{self.server.server_port}",
            "--engine", "fake-engine 0.1", "--model", "fake-model",
            "--hardware", "fake CPU", "--case", "short",
            "--warmups", "0", "--runs", "2", "--no-usage-request",
        ])
        receipt = probe.run(args)
        self.assertEqual(receipt["schema"], probe.SCHEMA)
        self.assertEqual(receipt["cases"][0]["summary"]["exact_answers"], 2)
        self.assertNotIn("127.0.0.1", json.dumps(receipt))
        self.assertNotIn("http", json.dumps(receipt))


if __name__ == "__main__":
    unittest.main()
