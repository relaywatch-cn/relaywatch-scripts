"""Run every detection script against the local mock (no real API). python3 -m unittest -v"""
import os, sys, json, unittest, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.dirname(HERE)]
import mock_server
SRV = mock_server.serve()
PORT = SRV.server_address[1]
import check_signature, check_format, check_billing, daily_prompts, check_speed_repeat, run_all

def use(variant):
    os.environ.update(RELAY_BASE_URL=f"http://127.0.0.1:{PORT}/{variant}", RELAY_API_KEY="test-key-not-real",
                      RELAY_CONFIRM_SPEND="yes")
    os.environ.pop("OFFICIAL_ANTHROPIC_KEY", None)

SYS = " ".join(f"w{i}" for i in range(1500))   # 1500 mock tokens
EXPECTED = 1500 + 1                             # system + "ok"

class T(unittest.TestCase):
    def test_honest_all_pass(self):
        use("honest")
        self.assertTrue(check_signature.run()["passed"])
        self.assertTrue(check_format.run()["passed"], check_format.run()["detail"])
        r = check_billing.run(expected_input=EXPECTED + 1, system_text=SYS + " honest")
        self.assertTrue(r["passed"], r["detail"])
        self.assertTrue(daily_prompts.run()["passed"])
        self.assertTrue(check_speed_repeat.run()["passed"])
    def test_nosig(self): use("nosig"); self.assertFalse(check_signature.run()["passed"])
    def test_forgedsig(self): use("forgedsig"); self.assertFalse(check_signature.run()["passed"])
    def test_inflated(self):
        use("inflated"); r = check_billing.run(expected_input=EXPECTED + 1, system_text=SYS + " infl")
        self.assertFalse(r["passed"]); self.assertFalse(r["detail"]["token_ok"])
    def test_nocache(self):
        use("nocache"); r = check_billing.run(system_text=SYS + " nc")
        self.assertFalse(r["passed"]); self.assertFalse(r["detail"]["cache_ok"])
    def test_wrongmodel(self):
        use("wrongmodel")
        self.assertIn("model_mismatch:claude-3-5-haiku-20241022", check_format.run()["detail"]["issues"])
        self.assertFalse(daily_prompts.run()["passed"])
    def test_badformat(self):
        use("badformat"); issues = check_format.run()["detail"]["issues"]
        self.assertIn("id_prefix", issues); self.assertIn("sse_start", issues)
    def test_slow(self):
        use("slow"); r = check_speed_repeat.run(); self.assertFalse(r["detail"]["speed_ok"])
    def test_repeat(self):
        use("repeat"); r = check_speed_repeat.run(); self.assertTrue(r["detail"]["identical"]); self.assertFalse(r["passed"])
    def test_spend_guard(self):
        use("honest"); os.environ["RELAY_CONFIRM_SPEND"] = "no"
        with self.assertRaises(SystemExit): check_format.run()
    def test_result_has_no_key(self):
        use("honest"); p = os.path.join(tempfile.mkdtemp(), "r.json"); run_all.main(p)
        with open(p) as f: s = f.read()
        self.assertNotIn("test-key-not-real", s); self.assertNotIn("SECRET=", s)
        self.assertTrue(all(x.get("passed") is not None for x in json.loads(s)), s)
if __name__ == "__main__": unittest.main(verbosity=2)
