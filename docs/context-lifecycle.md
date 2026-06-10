# Context Lifecycle

Context percentage is a heuristic. It should inform lifecycle decisions, not replace repo/test/product evidence.

For Fable-style 1M context:

- <50%: continue same lane if the work is coherent.
- 50-70%: finish current unit; bias toward handoff soon.
- >70%: close out and continue in a fresh lane.
- >85%: emergency closeout only.

A closeout prompt should be used once. After a handoff exists, start a fresh session or pause; do not repeatedly ask the old lane to close out.
