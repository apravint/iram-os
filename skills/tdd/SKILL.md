---
name: tdd
description: Test-driven development discipline. Use when building features, fixing bugs test-first, executing red-green-refactor cycles, or designing test seams.
---

# Test-Driven Development Protocol (Matt Pocock Architecture)

TDD is the **red ➔ green ➔ refactor** loop. This skill ensures that tests serve as enduring behavioral specifications rather than brittle reflections of internal implementation details.

---

## 🎯 What a Good Test Is

- **Tests verify behavior through public interfaces, not internal mechanics**: Code internals can change completely; tests shouldn't break.
- **Specification-style naming**: A test named `user can checkout with valid cart` describes an invariant business capability and survives massive internal refactoring.
- **Consult Domain Context**: Always read `GLOSSARY.md` (if it exists) so test names, mocks, and fixtures use consistent ubiquitous vocabulary.

---

## 🪡 Seams: Where Tests Go

A **seam** is the public boundary you test against — the exact interface where behavior is observed without reaching into internal private state.

1. **Test only at pre-agreed seams**: Before writing *any* test, identify the public boundary under test and verify it with the user.
2. **Prefer higher-level seams**: Test at the highest boundary that is still deterministic, fast, and gives actionable failure signal. The ideal number of testing seams per module is **one**.
3. **Seam Evaluation Matrix**: For any proposed seam, state:
   - What critical behaviors it verifies.
   - What edge cases it catches.
   - What implementation details it remains decoupled from.

---

## 🔄 The Strict Execution Loop

1. **RED**:
   - Write the minimal test asserting the desired behavior.
   - Run the test suite to **prove it fails for the expected reason** (not due to syntax or test harness configuration errors).
2. **GREEN**:
   - Write the simplest, most direct code that satisfies the test.
   - Do not optimize prematurely; prioritize correctness and passing status.
3. **REFACTOR**:
   - Remove duplication, enforce domain models, and improve ergonomics.
   - Rerun tests to ensure all invariants remain satisfied.

---

## 🚫 Testing Anti-Patterns to Avoid

- **Mocking internal collaborators**: Never mock internal helper functions or private classes. Mock only external I/O boundaries (HTTP, disk, third-party payment gateways).
- **Testing trivial getters/setters**: Focus testing investment on branching logic, state transitions, calculation math, and error handlers.
- **Flaky time/randomness**: Inject clock interfaces and seeded pseudorandom generators instead of relying on system wall clocks.
