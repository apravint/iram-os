---
name: diagnosing-bugs
description: Systematic diagnosis protocol for elusive bugs, flakiness, and performance regressions. Builds tight deterministic feedback loops and redacts secrets before debugging.
---

# Diagnosing Bugs Protocol (Matt Pocock Architecture)

A disciplined procedure for hard bugs. Skip phases only when explicitly justified.

> *"If you have a tight pass/fail signal for the bug (one that goes red on this bug), you will find the cause; bisection, hypothesis-testing, and instrumentation all just consume it. If you don't have one, no amount of staring at code will save you."*

---

## 🔒 Step 0: Secret Redaction

Always redact sensitive environment variables, auth tokens, and API credentials before showing output in logs or terminals:
- Replace credentials with `<REDACTED>`.
- Isolate test harnesses against dummy local environment variables.

---

## 🎯 Phase 1: Build a Tight Feedback Loop

Spend disproportionate effort here. The feedback loop must be:
- **Tight** (fast execution cycle, ideally < 3 seconds).
- **Red-capable** (it provably fails right now on the bug).
- **Deterministic** (runs without random network or timing flakes).

### Hierarchical Hierarchy of Feedback Loops:
1. **Failing Unit / Integration Test**: Minimal code exercising the public seam.
2. **Deterministic Script / Curl**: Replaying the failing HTTP payload or CLI invocation.
3. **Headless Browser Test**: Automated Playwright / Puppeteer script asserting on DOM state.
4. **Captured Trace Replay**: Replaying serialized production events or payload logs locally.
5. **Differential Harness**: Running identical inputs against old-version vs. new-version and diffing outputs.

> **Rule**: Do NOT formulate speculative hypotheses or guess at code fixes without first demonstrating a reproducible red feedback loop.

---

## 🔬 Phase 2: Scientific Hypothesis Isolation

Once a tight feedback loop is active:
1. State **one clear hypothesis** at a time.
2. Add minimal instrumentation (structured logs, assertions, bisection breakpoints) to test that hypothesis.
3. Observe the output of the feedback loop.
4. If disproven, discard the hypothesis and form the next one based on the new evidence.

---

## 🛠️ Phase 3: Root-Cause Remediation

1. Implement the minimal fix directly addressing the proven root cause.
2. Verify that the tight feedback loop turns **GREEN**.
3. Run the full regression test suite to ensure no other seams were impacted.
4. Remove temporary debug logs and commit the fix alongside the new regression test.
