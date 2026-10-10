---
name: wait-what
description: Cognitive circuit-breaker. Use when detecting contradictory requirements, impossible architectural assumptions, or severe conversational misalignment.
---

# Wait-What Protocol (Cognitive Circuit Breaker)

When an AI agent senses that the user's instructions or the codebase's state have hit a severe logical contradiction, proceeding blindly leads to compound errors, code churn, and broken abstractions.

The `wait-what` skill is an explicit **emergency stop** to pause execution and re-align before continuing.

---

## 🚨 Trigger Conditions

Activate this protocol immediately whenever:
1. **Contradictory Requirements**: Requirement A explicitly invalidates or conflicts with Requirement B.
2. **Impossible Invariants**: A request requires breaking a fundamental guarantee codified in `GLOSSARY.md` or existing ADRs.
3. **Severe Ambiguity**: A prompt can be interpreted in two mutually exclusive ways, each having radically different architectural consequences.
4. **Agent Loss-of-Clarity**: If you cannot succinctly summarize the problem in 2 sentences, stop and ask.

---

## 🛑 Action Protocol

When triggered:
1. **Halt execution**: Do not create files, edit code, or run destructive terminal commands.
2. **Re-pitch the situation**:
   - State what was requested.
   - State the exact point of friction, conflict, or confusion.
   - Use plain, unambiguous technical language (ASD-STE100 Simplified Technical English).
   - Use the project's established ubiquitous vocabulary.
3. **Present the Fork in the Road**:
   - Outline Option A (and its consequences).
   - Outline Option B (and its consequences).
   - Provide a clear recommendation.
4. **Wait for user intervention** before proceeding.
