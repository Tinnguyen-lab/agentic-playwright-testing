"""Real Chromium round-trip: login once, reuse state in later isolated runs."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs

from src.agents.execution_agent import ExecutionAgent
from src.models.playwright_artifacts import (
    ActionType, ExecStatus, GeneratedScript, LocatorStrategy, PlaywrightAction, PlaywrightPlan,
)
from src.services.browser_tasks import run_task
from src.services.script_template import render_script


class DemoAuthHandler(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass

    def _send(self, status, body="", **headers):
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name.replace("_", "-"), value)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        if self.path == "/login":
            self._send(200, '<label for="username">Username</label><input id="username">'
                            '<label for="password">Password</label><input id="password">'
                            '<button onclick="fetch(\'/session\',{method:\'POST\',body:'
                            'new URLSearchParams({u:document.querySelector(\'#username\').value,'
                            'p:document.querySelector(\'#password\').value})})'
                            '.then(r=>{if(r.ok)location.href=\'/dashboard\'})">Login</button>',
                       Content_Type="text/html")
        elif self.path in {"/dashboard", "/private"}:
            if "session=valid" not in self.headers.get("Cookie", ""):
                self._send(302, Location="/login")
            else:
                label = "Dashboard" if self.path == "/dashboard" else "Private profile"
                self._send(200, f"<h1>{label}</h1>", Content_Type="text/html")
        else:
            self._send(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        params = parse_qs(self.rfile.read(length).decode("utf-8"))
        if self.path == "/session" and params.get("u") == ["Admin"] and params.get("p") == ["admin123"]:
            self._send(200, "ok", Set_Cookie="session=valid; Path=/; HttpOnly; SameSite=Lax")
        else:
            self._send(401)


def _script(plan):
    return GeneratedScript(test_case_id=plan.test_case_id, code=render_script(plan))


def test_reuse_authenticated_state_across_snapshot_grounding_and_execution(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoAuthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        login = PlaywrightPlan(test_case_id="login", target_url=f"{origin}/login", actions=[
            PlaywrightAction(type=ActionType.GOTO, arg=f"{origin}/login"),
            PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.LABEL, value="Username", arg="Admin"),
            PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.LABEL, value="Password", arg="admin123"),
            PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
            PlaywrightAction(type=ActionType.EXPECT_URL, arg=f"{origin}/dashboard"),
        ])
        state = tmp_path / "auth.json"
        runner = ExecutionAgent()
        first = runner.run(_script(login), tmp_path / "runs", auth_state_save=state)
        assert first.status == ExecStatus.PASSED, first.stderr
        assert first.auth_state_saved and state.is_file()

        protected = PlaywrightPlan(test_case_id="private", target_url=f"{origin}/private", actions=[
            PlaywrightAction(type=ActionType.GOTO, arg=f"{origin}/private"),
            PlaywrightAction(type=ActionType.EXPECT_VISIBLE, strategy=LocatorStrategy.ROLE,
                             value="heading", role_name="Private profile"),
        ])
        unauthenticated = runner.run(_script(protected), tmp_path / "runs")
        assert unauthenticated.status == ExecStatus.FAILED

        snapshot = run_task("snapshot", {"url": f"{origin}/private", "storage_state": str(state)})
        assert "Private profile" in snapshot["snapshot"]
        grounded = run_task("ground", {"plan": protected.model_dump(mode="json"),
                                       "storage_state": str(state)})
        assert grounded["records"] and all(record["ok"] for record in grounded["records"])
        authenticated = runner.run(_script(protected), tmp_path / "runs", auth_state_in=state)
        assert authenticated.status == ExecStatus.PASSED, authenticated.stderr
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
