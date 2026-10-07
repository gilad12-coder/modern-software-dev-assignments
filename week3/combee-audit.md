# Combee implementation audit

GEPA's ComBEE strategy implements two-level aggregation and augmented shuffling when a component has at least four reflective records and at least two valid map outputs reach the reduce stage. It implements part of the method: the audited release has no dynamic batch-size controller. Smaller batches use a documented shortcut. The checks establish structure and call accounting; quality and speed remain unverified.

Sources: [Combee v2](https://arxiv.org/pdf/2604.04247v2), [GEPA at fb1ed58](https://github.com/gepa-ai/gepa/tree/fb1ed589fd83372caef499cffc2c73173d3b096b), and the [ACE grouping implementation at 82709de](https://github.com/ace-agent/ace/blob/82709de050e1db6e6ef2f07bcb0393560b94992a/ace/ace_batch.py#L750-L853).

## Requirement coverage

| Paper requirement | Implementation and evidence | Judgment |
|---|---|---|
| Two aggregation levels with `k = floor(sqrt(n))` groups (§3.1) | [Grouping and reduce path](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L348-L450). Tests and public-path diagnostics verify group counts, map calls, and a reduce prompt containing the intermediate proposals. | Matches on the normal path; exceptions below. |
| Duplicate records, default `p=2`, then shuffle (§3.2) | [Default](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L144) and [augmentation](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L382-L396). Tests verify two appearances per record. | Matches when the fallback is not taken. |
| Parallel map calls (§3.1, Figure 3) | [Batch dispatch](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L524-L573). Existing tests cover batched waves; plain callables run sequentially, as documented. | Requires `batch_reflection=True` and a batch-capable LM; actual concurrency and speed remain unmeasured. |
| Profile candidate sizes, fit epoch time, select a batch size (§3.3) | The [public API selects a fixed-size sampler](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/api.py#L369-L374). Source search and caller tracing found no bundled controller. | Discrepancy for the complete method. The module advertises only §§3.1 and 3.2. |
| Preserve the base method's update interface (§3) | Existing integration tests exercise `gepa.optimize` and `optimize_anything`; additional diagnostics exercise `gepa.optimize`. | Wiring verified with model doubles. |

## Findings

### Missing batch-size controller

The [module description](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L4-L21) scopes the implementation to aggregation and shuffling. The [blog describes the controller](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/docs/docs/blog/posts/2026-04-09-gepa-at-scale-with-combee/index.md#L83-L91) without explaining that it is absent from this release. Users choose the batch size themselves; GEPA tracks the missing controller in [issue #395](https://github.com/gepa-ai/gepa/issues/395). Clarify that scope in the usage documentation; full reproduction would require implementing and verifying the controller.

### Small-batch shortcut omits duplication

For one to three reflective records, the [fallback](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L355-L380) makes one ordinary reflection call, bypassing duplication and reduce. The [three-record test](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/tests/test_combee_reflection_lm.py#L105-L121) confirms this behavior. With ComBEE enabled, `gepa.optimize`'s default minibatch of 3 reaches this fallback when reflection produces one record per example. This is a documented departure from §3.2's default duplication. Retaining duplication would match that step; the paper does not explicitly discuss the `k=1` aggregation case. The effect on quality remains unverified.

### The blog uses the wrong starting batch size

The [blog's motivating example](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/docs/docs/blog/posts/2026-04-09-gepa-at-scale-with-combee/index.md#L63) associates the 87.0% to 72.5% accuracy change with batches of 3 and 100. Figure 2 of the paper shows batches of 1 and 100. Correct the starting value in the documentation.

## Unspecified choices

GEPA partitions the augmented records and distributes remainders across the first groups. Here `n` counts original records, so each map group receives about `p*n/k` record slots after duplication. For `n=40` and `p=2`, the group sizes are `14, 14, 13, 13, 13, 13`. The pinned ACE code uses the same group-size calculation. Its [configuration](https://github.com/ace-agent/ace/blob/82709de050e1db6e6ef2f07bcb0393560b94992a/ace/ace_batch.py#L121-L140) enables augmentation with factor 2 by default and sets it to 1 when augmentation is disabled.

The paper does not prescribe the exact GEPA reduce prompt, guarantee that duplicate copies enter different groups, or define recovery from malformed model outputs. GEPA's [single-surviving-proposal path](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/proposer/reflective_mutation/combee.py#L411-L439) skips reduce after other proposals fail to parse. That is a recovery choice whose quality effect remains unverified.

## Verification

The existing Combee suite passed all 55 tests. From the pinned GEPA repository root:

```sh
uv run --frozen --python 3.11 --with pytest pytest tests/test_combee_reflection_lm.py -q -p no:cacheprovider -m "not llm_live"
```

Public-path diagnostics with synthetic data, one component, and `p=2` observed the following for the first proposal in each run:

| Reflective records | Map groups | Total calls per proposal | Record slots across map calls |
|---|---|---|---|
| 9 | 3 | 4 | 18 |
| 40 | 6 | 7 | 80 |
| 60 | 7 | 8 | 120 |
| 84 | 9 | 10 | 168 |
| 94 | 9 | 10 | 188 |

The inspected reduce prompts contained the group proposals and no raw feedback. These diagnostics used scripted model doubles and shared synthetic training/validation data to inspect structure; their scores are not generalization measurements. The paper's benchmarks, real-provider behavior, and effects of the deviations remain unverified. No tracked GEPA files changed.
