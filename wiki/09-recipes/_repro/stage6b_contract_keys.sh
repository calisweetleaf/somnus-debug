#!/usr/bin/env bash
# Stage 6b: record the key sets of every machine-readable artifact the agent contracts rely on (needs stages 2-6).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage6b_contract_keys.log" 2>&1
cat > "$W/keys.py" <<'P'
import glob, json
r = json.load(open("/tmp/w4/proj/.somnus-debug/runs/latest.json"))
f = r["files"][0]
print("doctor top-level:", sorted(r))
print("doctor summary:", sorted(r["summary"]))
print("doctor issue:", sorted(r["issues"][0]))
print("doctor file:", sorted(f))
print("doctor file.metrics:", sorted(f["metrics"]))
print("doctor file.code_map:", sorted(f["code_map"]))
fn = next(x for x in r["files"] if x["functions"])["functions"][0]
print("doctor function:", sorted(fn))
cls = [c for x in r["files"] for c in x["classes"]]
print("doctor class:", sorted(cls[0]) if cls else "(no classes in this fixture)")
b1 = json.load(open("/tmp/w4/b1/out/report.json"))
print("doctor class (b1 fixture):", sorted(next(c for x in b1["files"] for c in x["classes"])))
print("doctor dependency_graph:", sorted(r["dependency_graph"]), "edge:", sorted(r["dependency_graph"]["edges"][0]))
print("doctor state_delta:", r["state_delta"])
d = json.load(open("/tmp/w4/proj/.somnus-debug/runs/delta.json"))
print("delta --json top-level:", sorted(d))
print("delta new[0]:", sorted(d["new"][0]))
m = json.load(open(sorted(glob.glob("/tmp/w4/proj_h2/test-runs/*/manifest.json"))[0]))
print("manifest top-level:", sorted(m), "schema_version", m["schema_version"])
print("manifest environment:", sorted(m["environment"]), "acceptance:", sorted(m["acceptance"]), "result:", sorted(m["result"]))
print("dispositions example:", json.load(open("/tmp/w4/proj/.somnus-debug/dispositions.json")))
P
run "python3 $W/keys.py"
