# Hermes scheduler-owner Windows reference consumer

This integration replays the exact isolated Hermes scheduler-owner producer and
its independent read-only auditor on a native GitHub-hosted Windows runner. It
is a downstream contract check, not a replacement implementation: source bytes
and provenance are fixed in `contract-sources.json` and checked before behavior
runs.

The native check proves three narrow properties:

1. the real Windows process is identified by matching boot time, PID, and
   centisecond process-start identity;
2. a stale heartbeat does not turn a live exact owner into absence; and
3. a process that actually exits is reported as `process_missing`.

The generated JSON receipt is metadata-only and intentionally declares
`safe_for_destructive_recovery=false`. It does not inspect command lines,
prompts, logs, or model output, and it never reads or edits a live Hermes store.

Run the portable source-binding check anywhere:

```bash
python3 -B integrations/hermes-owner-receipt/test_native_windows_contract.py
```

Run the full contract on Windows after installing the CI-only dependency:

```powershell
python -m pip install psutil==7.2.2
python -B integrations/hermes-owner-receipt/test_native_windows_contract.py
python -B integrations/hermes-owner-receipt/run_native_windows_contract.py --output windows-owner-contract-receipt.json
```
