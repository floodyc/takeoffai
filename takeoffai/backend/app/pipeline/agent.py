"""Phase 3: Agentic Refinement Orchestrator.

The orchestrator is a Sonnet LLM in a tool-use loop. It reviews the Phase 2
coarse detections and decides where to re-inspect at higher resolution.

This is the core differentiator: the agent applies domain knowledge
(suite patterns, corridor symmetry) and decides where to look harder.
"""

import json
import logging
import re
import time
from collections import Counter
from typing import Optional

import anthropic

from .config import PipelineConfig
from .models import Detection, DrawingContext, PhaseResult
from .prompts import ORCHESTRATOR_SYSTEM_PROMPT
from .rasterize import PageRenderer, image_to_base64
from .tools import TOOL_DEFINITIONS
from .vlm import inspect_crop

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Multi-turn tool-use orchestrator for fixture detection refinement."""

    def __init__(
        self,
        renderer: PageRenderer,
        cfg: PipelineConfig,
        context: Optional[DrawingContext],
        coarse_detections: list[Detection],
        on_progress: Optional[callable] = None,
    ):
        self.renderer = renderer
        self.cfg = cfg
        self.context = context
        self.detections = list(coarse_detections)
        self.on_progress = on_progress or (lambda *a: None)

        self.client = anthropic.AsyncAnthropic()
        self.vlm_calls = 0
        self.agent_log: list[dict] = []

    async def run(self) -> PhaseResult:
        """Execute the agentic refinement loop.

        Returns PhaseResult with any new detections found during refinement.
        """
        start = time.time()
        phase = PhaseResult(phase=3)
        new_detections = []

        remaining = self.cfg.max_vlm_calls_phase3
        if remaining <= 0:
            phase.duration_s = time.time() - start
            return phase

        # Build initial message
        messages = [{"role": "user", "content": self._build_initial_prompt()}]

        for iteration in range(self.cfg.max_agent_iterations):
            remaining = self.cfg.max_vlm_calls_phase3 - self.vlm_calls
            if remaining <= 0:
                logger.info("Phase 3: VLM budget exhausted")
                break

            try:
                response = await self.client.messages.create(
                    model=self.cfg.orchestrator_model,
                    max_tokens=self.cfg.orchestrator_max_tokens,
                    system=self._build_system_prompt(remaining),
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                )
            except Exception as e:
                logger.error(f"Phase 3 orchestrator error: {e}")
                phase.error = str(e)
                break

            # Append assistant response
            messages.append({"role": "assistant", "content": response.content})

            # Check for tool use
            tool_uses = [b for b in response.content if b.type == "tool_use"]

            if not tool_uses:
                # Agent sent text-only response or stopped
                if response.stop_reason == "end_turn":
                    logger.info("Phase 3: Agent ended turn without tools")
                    break
                continue

            # Execute tools
            tool_results = []
            for tu in tool_uses:
                self.agent_log.append({
                    "iteration": iteration,
                    "tool": tu.name,
                    "input": tu.input,
                })

                if tu.name == "finalize":
                    summary = tu.input.get("summary", "No summary")
                    logger.info(f"Phase 3: Finalized — {summary}")
                    self.agent_log.append({"finalize": summary})
                    phase.detections = new_detections
                    phase.vlm_calls = self.vlm_calls
                    phase.duration_s = time.time() - start
                    phase.metadata = {"agent_log": self.agent_log, "summary": summary}
                    return phase

                result, dets = await self._execute_tool(tu.name, tu.input)
                new_detections.extend(dets)
                self.detections.extend(dets)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                })

                self.on_progress(
                    "phase3",
                    f"Refinement step {iteration + 1}: {tu.name} "
                    f"({self.vlm_calls}/{self.cfg.max_vlm_calls_phase3} calls used)",
                )

            messages.append({"role": "user", "content": tool_results})

        phase.detections = new_detections
        phase.vlm_calls = self.vlm_calls
        phase.duration_s = time.time() - start
        phase.metadata = {"agent_log": self.agent_log}
        logger.info(
            f"Phase 3: {len(new_detections)} new detections, "
            f"{self.vlm_calls} VLM calls, {phase.duration_s:.1f}s"
        )
        return phase

    # ── Tool Execution ────────────────────────────────────────────────────

    async def _execute_tool(
        self, tool_name: str, tool_input: dict
    ) -> tuple[dict, list[Detection]]:
        """Execute a tool and return (result_dict, new_detections)."""

        if tool_name == "crop_and_inspect":
            return await self._tool_crop_and_inspect(tool_input)
        elif tool_name == "validate_pattern":
            return self._tool_validate_pattern(tool_input), []
        elif tool_name == "get_current_state":
            return self._tool_get_state(), []
        else:
            return {"error": f"Unknown tool: {tool_name}"}, []

    async def _tool_crop_and_inspect(
        self, params: dict
    ) -> tuple[dict, list[Detection]]:
        """Crop a region at high DPI and detect fixtures."""
        x_pct = params.get("x_pct", 50)
        y_pct = params.get("y_pct", 50)
        w_pct = min(params.get("width_pct", 25), 50)
        h_pct = min(params.get("height_pct", 25), 50)
        reason = params.get("reason", "targeted re-inspection")

        crop_img = self.renderer.render_crop(
            dpi=self.cfg.refine_dpi,
            x_pct=x_pct, y_pct=y_pct,
            w_pct=w_pct, h_pct=h_pct,
        )
        img_b64 = image_to_base64(crop_img, max_dim=self.cfg.max_image_dim)

        raw_dets = await inspect_crop(
            self.client, img_b64, self.cfg, self.context, reason
        )
        self.vlm_calls += 1

        # Convert to Detection objects
        detections = []
        for d in raw_dets:
            label = d.get("label", "").upper().strip()
            if not re.match(self.cfg.label_pattern, label):
                continue
            detections.append(Detection(
                label=label,
                variant=label[len(self.cfg.label_prefix):].lstrip("0123456789") or None,
                circuit=d.get("circuit"),
                room=d.get("room"),
                x=int(x_pct / 100 * self.renderer.render(self.cfg.coarse_dpi).size[0]),
                y=int(y_pct / 100 * self.renderer.render(self.cfg.coarse_dpi).size[1]),
                confidence=d.get("confidence", "MEDIUM"),
                on_boundary=False,
                source_phase=3,
                notes=f"Refinement: {reason}",
            ))

        return {
            "region": {"x_pct": x_pct, "y_pct": y_pct, "w_pct": w_pct, "h_pct": h_pct},
            "reason": reason,
            "detections_found": len(detections),
            "details": [d.to_dict() for d in detections],
        }, detections

    def _tool_validate_pattern(self, params: dict) -> dict:
        """Validate detection counts against expected patterns."""
        pattern = params.get("pattern_type", "all")
        results = {}

        if pattern in ("suite_kitchen", "all"):
            results["suite_kitchen"] = self._validate_suite_kitchen()

        if pattern in ("corridor", "all"):
            results["corridor"] = self._validate_corridor()

        return results

    def _validate_suite_kitchen(self) -> dict:
        """Check that each suite has expected kitchen fixtures."""
        suites = self.context.suites if self.context else []
        if not suites:
            return {"status": "no_suite_data", "message": "No suite info from context"}

        suite_numbers = {s.get("number") for s in suites if s.get("number")}
        prefix = self.cfg.label_prefix

        # Track which suites have each variant
        suites_with: dict[str, set] = {}  # variant → set of suite numbers
        for d in self.detections:
            room = (d.room or "").lower()
            for sn in suite_numbers:
                if sn.lower() in room or f"suite {sn}".lower() in room:
                    variant = d.label[len(prefix):].lstrip("0123456789") or "base"
                    if variant not in suites_with:
                        suites_with[variant] = set()
                    suites_with[variant].add(sn)

        # Find missing
        missing = {}
        for variant, found_in in suites_with.items():
            not_found = suite_numbers - found_in
            if not_found:
                missing[variant] = sorted(not_found)

        # Also check suites with NO detections at all
        all_detected_suites = set()
        for s in suites_with.values():
            all_detected_suites |= s
        no_detections = suite_numbers - all_detected_suites

        return {
            "total_suites": len(suite_numbers),
            "suites": sorted(suite_numbers),
            "variants_found": {k: sorted(v) for k, v in suites_with.items()},
            "missing": missing,
            "suites_with_no_detections": sorted(no_detections),
            "recommendation": (
                f"Re-inspect kitchens in suites: {', '.join(sorted(no_detections | set().union(*missing.values()) if missing else no_detections))}"
                if no_detections or missing
                else "All suites accounted for"
            ),
        }

    def _validate_corridor(self) -> dict:
        """Check corridor fixture patterns."""
        corridor_dets = [d for d in self.detections if "corridor" in (d.room or "").lower()]
        circuits = Counter(d.circuit for d in corridor_dets if d.circuit)

        return {
            "total_corridor_fixtures": len(corridor_dets),
            "by_circuit": dict(circuits),
            "by_label": dict(Counter(d.label for d in corridor_dets)),
            "by_confidence": dict(Counter(d.confidence for d in corridor_dets)),
        }

    def _tool_get_state(self) -> dict:
        """Return current detection state summary."""
        by_label = Counter(d.label for d in self.detections)
        by_room = Counter(d.room or "unknown" for d in self.detections)
        by_conf = Counter(d.confidence for d in self.detections)
        boundary = sum(1 for d in self.detections if d.on_boundary)

        return {
            "total_detections": len(self.detections),
            "by_label": dict(sorted(by_label.items())),
            "by_room": dict(sorted(by_room.items())),
            "by_confidence": dict(by_conf),
            "boundary_flags": boundary,
            "vlm_calls_used": self.vlm_calls,
            "vlm_calls_remaining": self.cfg.max_vlm_calls_phase3 - self.vlm_calls,
        }

    # ── Prompt Builders ───────────────────────────────────────────────────

    def _build_system_prompt(self, remaining: int) -> str:
        return ORCHESTRATOR_SYSTEM_PROMPT.format(
            drawing_context=json.dumps(self.context.to_dict(), default=str) if self.context else "Not available",
            detection_state=json.dumps(self._tool_get_state(), indent=2),
            remaining_calls=remaining,
        )

    def _build_initial_prompt(self) -> str:
        state = self._tool_get_state()
        return (
            f"Phase 2 coarse detection is complete. Here is the current state:\n\n"
            f"```json\n{json.dumps(state, indent=2)}\n```\n\n"
            f"You have {self.cfg.max_vlm_calls_phase3} VLM calls for refinement.\n\n"
            f"Start by calling validate_pattern with pattern_type='all' to identify gaps, "
            f"then use crop_and_inspect for targeted re-inspection of problem areas. "
            f"Call finalize when you are satisfied with the count."
        )
