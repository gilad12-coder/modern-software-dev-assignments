# Evidence and judgment

## When similar code means different behavior

**Delegation is only one part of fidelity.** A wrapper can import the original optimizer while changing its inputs, search space, budget accounting, or selection. Audit the relevant adapter and configuration alongside the dependency. If the pinned dependency cannot be inspected, keep delegated behavior unverified.

**Labels do not establish independent data.** Separate `train` and `development` identifiers can still wrap the same examples. Trace the payloads and their provenance. A rerun on the same examples may measure repeatability, but it does not establish generalization to a separate development set.

**The newest candidate is not necessarily the selected candidate.** Distinguish proposal, acceptance, development ranking, and final return. A test where every candidate improves cannot distinguish returning the last candidate from returning the best development-scored one. A later accepted candidate with a worse development score is a more informative case.

**Operators and units matter.** Check strict versus non-strict improvement, min versus max objectives, per-example versus aggregate scores, tie handling, and whether a budget counts proposals, model calls, or task evaluations. A counter with the same numeric value can represent different work.

**Intent does not erase a difference.** A documented shortcut can be an intentional adaptation while remaining inconsistent with the paper's method or experimental claims. State both the rationale that is actually documented and the consequence. If no rationale exists, do not invent one.

**Different code can be equivalent.** Refactoring, batching, caching, or vectorization may preserve the specified behavior. Identify the invariant and the conditions under which it holds. For stochastic behavior, the same seed or one matching result is not proof that the distributions are equivalent.

**Implementation fidelity and experimental reproduction are separate claims.** A different model, dataset, or search budget can leave the core method intact while preventing reproduction of the reported experiment. Conversely, a similar score does not prove the method was implemented faithfully.

## Evidence strength

Prefer the versioned method or pinned official code for what is required, reachable implementation code for what is implemented, and targeted tests or run artifacts for what happened. Comments and documentation can establish claimed intent but cannot override contradictory behavior. Old chats are leads to investigate, not current implementation evidence.

A passing mock-based test supports only the boundary it exercises. An unavailable dependency, skipped integration test, or unrun benchmark remains a limitation. State a proposed discriminating test as a proposal until it has actually run.

## Worked examples

These examples are illustrative, not findings about the repository being audited.

| Reference and observed code | Assessment | Useful conclusion |
|---|---|---|
| The method requires separate development examples. An adapter passes the training examples under new development IDs and documents that it deliberately re-scores those same examples. | Intentional adaptation | The adapter changes the validation protocol. Re-scoring can check repeatability but cannot support a claim of independent development-set generalization. |
| The reference returns the highest development-scored candidate. Candidate A scores 0.9; later candidate B is accepted on a training batch but scores 0.8 on development. The return path chooses B because it is newest. | Discrepancy | Return selection violates the development-best rule. A test containing only monotonically improving candidates would miss it; this two-candidate case distinguishes the behaviors. |
| An adapter selects a policy called `StrictImprovement`, but its pinned dependency is unavailable and all tests replace the policy with a mock. | Insufficient evidence | The adapter selects that policy; whether ties are rejected remains unverified. Inspect the pinned implementation or test its tie behavior. |
| A paper specifies selection after a completed run but says nothing about cancellation. An adapter documents returning its last checkpoint when canceled. | Insufficient evidence | The fallback is documented, but there is no paper requirement to preserve or change. Describe the fallback without calling it equivalent or an intentional adaptation of the paper. |

## Compact report shape

Start with the scope and conclusion: what was checked, whether that part matches, and the material limitation. Identify the repository commit and paper version or upstream commit. Note relevant uncommitted changes if reviewing the working tree.

| Requirement and comparison source | Implementation evidence | Assessment | Test evidence and consequence |
|---|---|---|---|
| A specific obligation and its source location, or explicitly "not specified" | Reachable symbol and verified location, including relevant configuration | Equivalent / Intentional adaptation / Discrepancy / Insufficient evidence | Actual test status; what this means for the claimed behavior |

End with actionable corrections or the smallest checks needed to resolve uncertainty. Omit generic recommendations and a numeric fidelity percentage. A bounded review with unresolved evidence is more useful than a blanket assurance.
