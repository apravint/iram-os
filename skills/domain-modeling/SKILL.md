---
name: domain-modeling
description: Build, encode, and sharpen a project's domain model into types and invariants. Use when discussing codebase terminology, writing or editing GLOSSARY.md, or recording ADRs.
---

# Domain Modeling & Ubiquitous Language (Matt Pocock Architecture)

Actively build and sharpen the project's domain model as you design. 

> *"With a ubiquitous language, conversations among developers and expressions of the code are all derived from the same domain model."* — Eric Evans, Domain-Driven Design

Agents frequently drop into codebases and guess at terminology, resulting in verbose 20-word descriptions where 1 precise term will do. This skill establishes a single shared language between human engineers and AI agents, encoding business invariants directly into the type system and architectural documentation.

---

## 📂 Repository Structure

Most repositories operate with a single bounded context:

```text
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If multiple bounded contexts exist, create a root `GLOSSARY-MAP.md` pointing to sub-contexts:

```text
/
├── GLOSSARY-MAP.md
├── docs/adr/                # System-wide architectural decision records
└── src/
    ├── ordering/
    │   ├── GLOSSARY.md
    │   └── docs/adr/
    └── billing/
        ├── GLOSSARY.md
        └── docs/adr/
```

> **Create files lazily**: Only create `GLOSSARY.md` or `docs/adr/` when the first domain term crystallizes or when the first architectural tradeoff is decided.

---

## 📐 Type-Driven Invariants

When modeling domain concepts into code:
1. **Make illegal states unrepresentable**: Use tagged unions (discriminated unions) rather than optional properties that allow impossible combinations.
2. **Branded Types**: Use branded primitives (`type UserId = string & { readonly __brand: unique symbol }`) to prevent passing a `CompanyId` where a `UserId` is expected.
3. **Parse, Don't Validate**: Validate domain inputs at the system boundary (API / CLI) and transform them into rich, validated domain types before core logic touches them.

---

## 📝 `GLOSSARY.md` Format Standard

```markdown
# Ubiquitous Language Glossary

### [Term Name]
- **Definition**: The unambiguous meaning of this term within this domain.
- **Synonyms / Discarded Names**: Terms we deliberately do *not* use to avoid confusion.
- **Invariant Rules**: Non-negotiable business rules governing this concept.
- **Code Representation**: The concrete type or interface representing this concept.
```

---

## 🏛️ Architecture Decision Records (`docs/adr/XXXX-title.md`)

When an architectural tradeoff is finalized during a session:
1. **Title**: Short, active phrase (e.g. `0003-use-socket2-for-hyprland-ipc.md`).
2. **Status**: `PROPOSED`, `ACCEPTED`, or `DEPRECATED`.
3. **Context**: What problem forced this decision?
4. **Decision**: What did we decide to do?
5. **Consequences**: What becomes easier? What becomes harder or requires future migration?
