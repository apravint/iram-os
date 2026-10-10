---
name: to-spec
description: Synthesize conversational context and design discussions into formal engineering specifications without conducting repetitive interviews.
---

# To-Spec Protocol (Matt Pocock Architecture)

This skill synthesizes conversational context, codebase architecture, and prior design discussions into a formal, actionable technical specification. 

**Guideline**: Do not re-interview the user; synthesize and formalize what has already been decided.

---

## 🧭 Workflow

1. **Explore the Codebase**: Map existing modules, review `GLOSSARY.md` for consistent domain vocabulary, and respect relevant ADRs.
2. **Propose Seams**: Identify the highest public seams where the feature will be tested and integrated. Confirm the seam with the engineer.
3. **Format the Specification**: Use the standard template below to publish the spec to the issue tracker or docs directory.

---

## 📑 Specification Standard Template

```markdown
# Specification: [Feature Name]

## 1. Problem Statement
The precise friction, bottleneck, or limitation from the end-user or developer's perspective.

## 2. Desired Outcomes & Acceptance Criteria
- [ ] Invariant A is satisfied under condition X.
- [ ] Invariant B handles edge condition Y cleanly.
- [ ] Public seam behaves as expected.

## 3. Public Seams & Interfaces
- Describe the exact public boundary under test.
- Document input/output types and signatures.

## 4. Implementation Plan
1. Step 1: Types and domain invariants.
2. Step 2: Red test asserting failure.
3. Step 3: Minimal implementation.
4. Step 4: Verification and integration.

## 5. Architectural Trade-offs & ADR Reference
- Link to relevant Architecture Decision Record or record new decisions.
```
