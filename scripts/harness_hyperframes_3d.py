"""Brain Autopilot Declarative Harness for HyperFrames Pro v2.0 (GSAP + Three.js 3D WebGL)."""

from brain_autopilot.kit import *
import lib


class HyperFrames3DVerificationHarness(Harness):
    goal = (
        "Verify deterministic GSAP + Three.js 3D virtual-clock seeking across all 3 timeline beats "
        "and 3D wireframe shader mode with zero console, network, WebGL, or layout errors."
    )
    start_route = "/index.html?autopilot=1"
    stall_seconds = 25.0

    def setup(self, app):
        self.plan = [
            Step(
                "seek_opening_beat",
                "Scrub virtual clock to Beat 1 (0.45s) and verify headline reveal",
                done=lambda o: "BEAT_1_OPENING" in o["beat_status"],
                options=["scrub_beat_1", "inspect_initial_stage"],
            ),
            Step(
                "seek_orbit_beat",
                "Scrub virtual clock to Beat 2 (1.80s) and verify 3D orbit & telemetry cards",
                done=lambda o: "BEAT_2_ORBIT" in o["beat_status"],
                options=["scrub_beat_2", "scrub_beat_1"],
            ),
            Step(
                "toggle_threejs_wireframe",
                "Toggle Three.js 3D material pass to architectural wireframe",
                done=lambda o: "3D_WIREFRAME_PASS" in o["three_status"],
                options=["switch_3d_wireframe", "scrub_beat_2"],
            ),
            Step(
                "seek_final_hold",
                "Scrub virtual clock to Beat 3 (4.60s) and verify clean ending hold",
                done=lambda o: "BEAT_3_HOLD" in o["beat_status"] and "3D_WIREFRAME_PASS" in o["three_status"],
                options=["scrub_beat_3", "switch_3d_wireframe"],
            ),
        ]

    def observe(self, app):
        route, beat_txt, three_txt, errs, net_errs, metrics, findings = app.batch([
            lambda: app.route(),
            lambda: str(app.get("[data-testid='beat-status']", "text") or ""),
            lambda: str(app.get("[data-testid='three-status']", "text") or ""),
            lambda: app.console_errors(),
            lambda: app.network_errors(),
            lambda: app.metrics(),
            lambda: app.findings(),
        ])
        return {
            "route": route,
            "beat_status": beat_txt,
            "three_status": three_txt,
            "console_errors": len(errs),
            "network_errors": len(net_errs),
            "canvas_present": bool(metrics.get("canvas_present", True)),
            "canvas_blank": bool(metrics.get("canvas_blank", False)),
            "webgl_errors": int(metrics.get("webgl_errors", 0) or 0),
            "findings_count": len(findings),
        }

    def options(self, obs):
        return [
            Option(
                "scrub_beat_1",
                "Scrub timeline to Beat 1 (0.45s Opening)",
                lambda app, o: lib.scrub_to_beat(app, "seek-beat-1", "BEAT_1_OPENING"),
                effect=lambda before, after: "BEAT_1_OPENING" in after["beat_status"],
            ),
            Option(
                "inspect_initial_stage",
                "Wait for initial 3D stage and GSAP fonts to settle",
                lambda app, o: wait_for_settled(app, timeout=1.0),
                effect=lambda before, after: after["canvas_present"],
            ),
            Option(
                "scrub_beat_2",
                "Scrub timeline to Beat 2 (1.80s Mid Orbit)",
                lambda app, o: lib.scrub_to_beat(app, "seek-beat-2", "BEAT_2_ORBIT"),
                effect=lambda before, after: "BEAT_2_ORBIT" in after["beat_status"],
            ),
            Option(
                "switch_3d_wireframe",
                "Toggle Three.js 3D stage to Wireframe Pass",
                lambda app, o: lib.toggle_threejs_pass(app, "3D_WIREFRAME_PASS"),
                effect=lambda before, after: after["three_status"] != before["three_status"],
            ),
            Option(
                "scrub_beat_3",
                "Scrub timeline to Beat 3 (4.60s Final Clean Hold)",
                lambda app, o: lib.scrub_to_beat(app, "seek-beat-3", "BEAT_3_HOLD"),
                effect=lambda before, after: "BEAT_3_HOLD" in after["beat_status"],
            ),
        ]

    def status(self, obs):
        if obs["console_errors"] > 0 or obs["network_errors"] > 0 or obs["webgl_errors"] > 0:
            return Status("failed", "Console, network, or WebGL error detected during timeline seek", obs)
        if "BEAT_3_HOLD" in obs["beat_status"] and "3D_WIREFRAME_PASS" in obs["three_status"]:
            return Status("done", "All 3 timeline beats and Three.js 3D passes verified cleanly", obs)
        return Status()
