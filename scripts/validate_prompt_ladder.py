from __future__ import annotations
import argparse
from pathlib import Path

TARGETS={
"task-intake-prompt.md","design-spec-prompt.md","implementation-plan-prompt.md","execute-next-action-prompt.md",
"debug-incident-prompt.md","live-run-prompt.md","parallel-change-prompt.md","verification-closeout-prompt.md",
"documentation-update-prompt.md","publication-prompt.md","drift-reconciliation-prompt.md","code-review-prompt.md"}

def validate_prompt_ladder(root: Path) -> list[str]:
    folder=root/"docs/operating_system/prompt_templates"
    actual={path.name for path in folder.glob("*-prompt.md")}
    findings=[]
    for name in sorted(TARGETS-actual): findings.append(f"missing prompt: {name}")
    for name in sorted(actual-TARGETS): findings.append(f"superseded prompt remains: {name}")
    return findings

def main(argv=None):
    parser=argparse.ArgumentParser(description="Validate canonical prompt inventory.")
    parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    args=parser.parse_args(argv)
    findings=validate_prompt_ladder(Path(args.repo_root))
    if findings:
        print("Prompt inventory validation failed:")
        for finding in findings: print(f"- {finding}")
        return 1
    print("Prompt inventory validation passed.")
    return 0

if __name__=="__main__": raise SystemExit(main())
