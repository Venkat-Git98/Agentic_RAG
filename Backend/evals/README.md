# Evals

How this project measures whether its answers are right, and how it notices when they get worse.

## The idea in one minute

A RAG system can fail in two places: it can **retrieve** the wrong part of the code, or it can retrieve the right part and still **answer** badly. So there are two evals, plus live monitoring:

| | What it checks | Uses a model? | Speed | When it runs |
|---|---|---|---|---|
| `retrieval_eval` | Is the right section in the top results? | no | ~20 s | every push |
| `e2e_eval` | Is the final answer right, cited, and fast? | yes (the app itself) | ~1 min per question | nightly |
| `/api/metrics` | How is the deployed app behaving for real users? | no | live | always |

All of them depend on one thing: a **golden dataset**, a list of questions whose correct answer is known.

## 1. The golden dataset: `golden.jsonl`

One question per line:

```json
{"id": "court-width", "type": "factual", "question": "What is the minimum width of a court?",
 "expected": ["1205.3"], "facts": ["3 feet"]}
```

- `expected`: the sections or tables that contain the answer. A result under an expected section also counts (`903` accepts `903.2.1`). Tables are written `table:1607.1`.
- `facts`: short strings a correct answer must contain (a number, a standard name).
- `type`: `factual` (plain question), `table` (answer is in a table), `direct` (names a section), `not_in_graph` (the code graph does not cover it, so the right behaviour is a web fallback, not an invented citation).

Rules for adding questions:

1. Write the question the way a user would, without copying the section's wording.
2. Take `expected` and `facts` from the code text itself, never from the app's answer.
3. Run `python -m evals.check_dataset`. It confirms every expected section exists in the graph and every fact appears in its text. An eval is only as trustworthy as its answer key.
4. When a user reports a bad answer, add that question. That is how the set grows where it matters.

## 2. Retrieval eval

```bash
python -m evals.retrieval_eval                  # the retriever as the app uses it
python -m evals.retrieval_eval --variant all    # every variant side by side
```

Metrics:

- **hit@k**: share of questions whose expected section is among the top k results. The app passes 5 results to the model, so hit@5 is "did the model get the right text at all" and hit@1 is "was it the first thing it read".
- **MRR** (mean reciprocal rank): 1 for rank 1, 1/2 for rank 2, 0 for a miss, averaged. One number that rewards ranking the right section higher.

`--variant all` is an **ablation**: the same retriever with one thing changed at a time, so each row shows what that change is worth.

| variant | what changed | hit@1 | hit@3 | MRR |
|---|---|---|---|---|
| `legacy` | the old path: question embedded as a document | 57% | 80% | 0.69 |
| `query-embed` | question embedded as a query | 88% | 96% | 0.92 |
| `all-indexes` | also search table and diagram embeddings | 86% | 96% | 0.91 |
| `fulltext` | keyword search only | 55% | 74% | 0.66 |
| `fused` | vector + keyword, equal votes | 65% | 80% | 0.76 |
| `hybrid-plain` | vector + sections named in the question | 94% | 100% | 0.97 |
| `hybrid-context` | same, embeddings include the section header | **98%** | **100%** | **0.99** |

(49 questions, October 2026.)

What these numbers decided:

- One wrong parameter (`task_type`) was costing 31 points of hit@1.
- Fusing keyword search into the ranking sounded right and made it **worse** (88% to 65%). Without the eval that change would have shipped. Keyword search is kept only as the fallback when the embedding service is down.
- Embedding each passage with its chapter/section header was worth another 4 points.

A caution: 49 questions is small, and the weights were chosen on these same questions. Treat a 2 to 4 point difference as noise, and add questions before tuning further.

## 3. End-to-end eval

```bash
python -m evals.e2e_eval --sample 10                      # against a local server on :8030
python -m evals.e2e_eval --base-url https://agenticrag-production.up.railway.app --sample 10
python -m evals.e2e_eval --judge                          # all questions, with the model judge
```

It calls `/api/chat` exactly as the website does, with the answer cache off, and grades each answer:

- **answered**: an answer came back without an error.
- **citation hit**: the answer cites an expected section that really exists in the graph.
- **fact recall**: share of the expected facts found in the answer. Cheap and strict, but blind to paraphrase ("three feet" will not match "3 feet").
- **web fallback**: should be near 0 for questions the graph covers, and 1 for `not_in_graph` questions.
- **seconds**: time to the complete answer.
- **judge** (`--judge`): a model reads the real code text and the answer and scores 1 to 5. It catches what string matching cannot, but it is a model's opinion: read a sample of its verdicts before trusting the average.

The same 12 questions before and after the retrieval rewrite (October 2026):

| | before | after |
|---|---|---|
| citation hit | 67% | **100%** |
| web fallback on questions the graph covers | 67% | **33%** |
| judge score (1 to 5) | 4.75 | 5.0 |
| median seconds | 83 | 79 |

Reading it: the old pipeline often failed to find the section, searched the web instead, and still produced a plausible answer, which is why the judge score barely moved while citation hit jumped. A judge that scores almost everything 5 is too lenient to separate good from great, so citation hit and web fallback are the numbers to watch here. Latency did not move because it is spent in the model calls, not in retrieval.

## 4. Monitoring

**In CI** (`.github/workflows/evals.yml`)

- Every push that touches `Backend/`: dataset check + retrieval eval with a bar (`--min-hit3 0.95 --min-mrr 0.90`). A change that breaks retrieval turns the run red.
- Nightly: end-to-end eval on 8 questions against the deployed app, plus the live metrics, written to the run summary.

**Live** (`GET /api/metrics?days=7`)

Every answered question stores a small record (no question or answer text): latency, route, whether the web fallback was used, how many code sections were cited. The endpoint returns totals and one row per day:

- `latency_p50_s`, `latency_p95_s`: typical and slow-case answer time
- `web_fallback_rate`: rising means retrieval is failing, or users ask about chapters the graph lacks
- `no_citation_rate`: answers that cite nothing from the code
- `error_rate`

Offline evals tell you a change is safe before it ships. Live metrics tell you what real questions look like, and they are where the next golden questions come from.

## Workflow for any retrieval or prompt change

1. `python -m evals.retrieval_eval --variant all` before the change (the result is saved in `results/`).
2. Make the change.
3. Run it again and compare. If a number dropped, look at the listed misses before deciding.
4. For prompt or agent changes, run `e2e_eval --sample 10` before and after as well.
5. If the change affects answers, bump `CACHE_VERSION` in `core/answer_cache.py` so old cached answers are not served.
