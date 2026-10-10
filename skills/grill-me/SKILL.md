---
name: grill-me
description: Interview the user relentlessly about a plan, architectural decision, or idea to eliminate ambiguity and stress-test assumptions before coding.
---

# Grill-Me Protocol (Matt Pocock Architecture)

Interview the user relentlessly until you reach an ironclad, shared understanding. 

Developing real applications is hard, and the most common failure mode in software development is misalignment. You think the agent knows what you want; then you see what it built, and you realize it didn't understand the core problem at all.

This skill runs a **grilling session** to eliminate the communication gap between the human engineer and the AI.

---

## 🌲 The Design Tree Concept

Map the architectural space as a **design tree**:
- Every foundational decision branches into sub-decisions that depend on it.
- Never ask questions about distant branches when the trunk or root decision is still unsettled.

## 🔁 Working in Rounds

Work the design tree in strict **rounds**:
1. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask *now* without guessing at answers you haven't heard yet.
2. Ask the entire frontier in one round:
   - Number each question.
   - Provide concrete options and trade-offs.
   - **Always state your recommended answer with rationale (`➡️ Recommended: ...`)**.
3. **Wait for the user's answers** before generating subsequent questions or writing code.

---

## 📋 Round Formatting Standard

Format each round using this precise structure:

```markdown
❓ **Q1** - **<Decision Area>**: <Context explaining why this decision matters, edge cases, and options>

➡️ **Recommended**: <Your recommended decision with technical rationale>

---

❓ **Q2** - **<Decision Area>**: <Context explaining why this decision matters, edge cases, and options>

➡️ **Recommended**: <Your recommended decision with technical rationale>
```

---

## 🛑 Rules of Engagement

1. **No premature code**: Do not write implementation code until the active round has converged and core architectural invariants are settled.
2. **Surface hidden trade-offs**: Explicitly highlight data durability, latency, type safety, operational complexity, and migration friction.
3. **Be opinionated, not stubborn**: Recommend the cleanest, most maintainable path, but pivot immediately when the user provides domain constraints.
4. **Transition smoothly**: Once the grilling rounds converge, graduate directly to writing specs (`to-spec`), domain models (`domain-modeling`), or test seams (`tdd`).
