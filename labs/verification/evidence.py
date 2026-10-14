"""Build scoped requirement evidence from existing runner reports, without running tools."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {"pass", "fail", "not_run", "unknown", "not_applicable"}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes package: {name}")
    return path

def checked_record(root, report, name, sources, markers):
    record = report.get("labs", {}).get(name)
    if not record:
        raise ValueError(f"Missing required lab record: {name}")
    if record.get("status") not in {"pass", "fail"}:
        raise ValueError(f"Unrecognized runner status: {name}")
    if record.get("student_rtl"):
        raise ValueError("Reference plan requires reference RTL; create a reviewed variant plan for student overrides")
    for source in sources:
        path = inside(root, source)
        if not path.is_file() or report.get("sources", {}).get(source) != digest(path):
            raise ValueError(f"Missing/stale source identity: {source}")
    artifacts = record.get("artifacts", {})
    for name, expected in artifacts.items():
        path = inside(root, name)
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"Missing/stale artifact: {name}")
    commands = record.get("commands", [])
    if not commands:
        raise ValueError("A result requires command records")
    logs = []
    for command in commands:
        name = command.get("log", "")
        if name not in artifacts:
            raise ValueError(f"Command log is not in the artifact identity record: {name}")
        logs.append(inside(root, name).read_text(encoding="utf-8", errors="replace"))
    if record["status"] == "pass":
        if any(type(c.get("returncode")) is not int or c["returncode"] != 0 for c in commands):
            raise ValueError("PASS record contains an incomplete or failed command")
        text = "\n".join(logs)
        for marker in markers:
            if marker not in text:
                raise ValueError(f"Expected checker completion is missing: {marker}")
    return record

def build(root, plan, reports):
    results=[]
    identifiers=set()
    for requirement in plan["requirements"]:
        identifier=requirement["id"]
        if identifier in identifiers:
            raise ValueError(f"Duplicate requirement ID: {identifier}")
        identifiers.add(identifier)
        result={k: requirement[k] for k in ("id", "requirement", "level", "scope", "coverage")}
        origin=requirement.get("evidence")
        if origin:
            report=reports.get(origin["report"])
            if report is None:
                result.update(status="not_run", rationale="Required report not supplied")
            else:
                record=checked_record(root,report,origin["lab"],plan["sources"][origin["report"]],origin.get("markers", []))
                result.update(status=record["status"], seed=record.get("seed"),
                              commands=record["commands"], artifacts=record["artifacts"],
                              environment=report.get("environment", {}))
        else:
            status=requirement["status"]
            if status not in STATUSES or status in {"pass", "fail"}:
                raise ValueError("A test result requires evidence; static rows may only describe unresolved or inapplicable checks")
            if not requirement.get("rationale"):
                raise ValueError(f"Status needs a rationale: {identifier}")
            result.update(status=status,rationale=requirement["rationale"])
        results.append(result)
    return {"schema_version":1,"project":plan["project"],
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "claim":"Scoped runner-level evidence, not functional cross-coverage or physical signoff",
            "requirements":results,
            "summary":{s:sum(r["status"]==s for r in results) for s in sorted(STATUSES)}}

def exit_status(evidence, plan):
    required={r["id"] for r in plan["requirements"] if r.get("required_reference", False)}
    return int(any(r["status"]=="fail" or (r["id"] in required and
                   r["status"] not in {"pass", "not_applicable"}) for r in evidence["requirements"]))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,default=Path(__file__).with_name("project-plan.json"))
    parser.add_argument("--unit-report",type=Path,required=True)
    parser.add_argument("--system-report",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    reports={name:json.loads(path.read_text(encoding="utf-8")) if path else None
             for name,path in [("unit",args.unit_report),("system",args.system_report)]}
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    evidence=build(ROOT,plan,reports)
    evidence["plan_sha256"]=digest(args.plan)
    evidence["collector_sha256"]=digest(Path(__file__))
    evidence["report_sha256"]={name:digest(path) for name,path in [("unit",args.unit_report),("system",args.system_report)] if path}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(evidence["summary"],sort_keys=True))
    return exit_status(evidence, plan)

if __name__=="__main__":
    try:
        sys.exit(main())
    except (ValueError,KeyError,OSError,json.JSONDecodeError) as error:
        print(f"FAIL evidence: {error}",file=sys.stderr)
        sys.exit(1)
