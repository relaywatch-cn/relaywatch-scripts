"""End-to-end: run_all.main() against every mock variant (stream + non-stream), validate result JSON
against the submission schema, and confirm no key/prompt leakage. No real API calls."""
import os, sys, json, unittest, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mock_server
SRV = mock_server.serve(); PORT = SRV.server_address[1]
import run_all, validate_result
KEY = "sk-ant-TESTKEY-not-real-0123456789"
# check -> expected passed value per variant (None = not asserted)
EXPECT = {
 "honest":     {"signature": True,  "format": True,  "billing": True,  "daily_prompts": True,  "speed_repeat": True},
 "nosig":      {"signature": False},
 "forgedsig":  {"signature": False},
 "inflated":   {"billing": False},
 "wrongmodel": {"format": False, "daily_prompts": False},
 "nocache":    {"billing": False},
 "slow":       {"speed_repeat": False},
 "repeat":     {"speed_repeat": False},
 "badformat":  {"format": False},
}
class E2E(unittest.TestCase):
    def _run(self, variant):
        os.environ.update(RELAY_BASE_URL=f"http://127.0.0.1:{PORT}/{variant}", RELAY_API_KEY=KEY, RELAY_CONFIRM_SPEND="yes")
        os.environ.pop("OFFICIAL_ANTHROPIC_KEY", None)
        # 1500 mock tokens + 1 for "ok"; billing uses random system text of 1500 words
        os.environ["EXPECTED_INPUT_TOKENS"] = "1501"
        p = os.path.join(tempfile.mkdtemp(), "result.json"); out = run_all.main(p)
        with open(p) as f: raw = f.read()
        return out, raw
    def test_variants(self):
        for v, exp in EXPECT.items():
            with self.subTest(variant=v):
                out, raw = self._run(v)
                errs = validate_result.validate(json.loads(raw), secrets=[KEY])
                self.assertEqual(errs, [], f"{v}: {errs}")
                self.assertNotIn(KEY, raw); self.assertNotIn("TESTKEY", raw)
                got = {r["check"]: r["passed"] for r in out}
                self.assertEqual(len(got), 5)
                for c, want in exp.items(): self.assertEqual(got[c], want, f"{v}/{c}: {out}")
                if v != "honest": self.assertIn(False, got.values())
                st = mock_server.State.calls
                self.assertGreater(st.get((v, True), 0), 0, "no streaming request")
                self.assertGreater(st.get((v, False), 0), 0, "no non-stream request")
    def test_validator_rejects_leaks(self):
        bad = [{"check": "format", "passed": True, "relay_host": "x", "date": "2026-10-19", "script_version": "0",
                "detail": {"prompt": "Compute ((1*2)+3)-4*5", "api_key": KEY}}]
        errs = validate_result.validate(bad, secrets=[KEY])
        self.assertTrue(any("forbidden" in e for e in errs)); self.assertTrue(any("leak" in e or "secret" in e for e in errs))
if __name__ == "__main__": unittest.main(verbosity=2)
