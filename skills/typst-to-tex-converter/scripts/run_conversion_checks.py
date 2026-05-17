#!/usr/bin/env python3
"""Run Typst-to-TeX audit before any TeX build.

This wrapper makes the verification order mechanical: the build command is
skipped unless the audit passes for the current output file.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_typ", type=Path)
    parser.add_argument("output_tex", type=Path)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--tex-evidence", type=Path, default=None)
    parser.add_argument("--no-fix", action="store_true")
    parser.add_argument("build_cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    audit = Path(__file__).with_name("audit_tex_conversion.py")
    audit_cmd = [str(audit), str(args.source_typ), str(args.output_tex)]
    if not args.no_fix:
        audit_cmd.append("--fix")
    if args.ledger:
        audit_cmd.extend(["--ledger", str(args.ledger)])
    if args.tex_evidence:
        audit_cmd.extend(["--tex-evidence", str(args.tex_evidence)])

    audit_result = subprocess.run(audit_cmd, check=False, text=True, capture_output=True)
    if audit_result.stdout:
        print(audit_result.stdout, end="")
    if audit_result.stderr:
        print(audit_result.stderr, end="", file=sys.stderr)
    if audit_result.returncode != 0:
        first_detail = ""
        in_fail = False
        for line in audit_result.stdout.splitlines():
            if line == "FAIL:":
                in_fail = True
                continue
            if in_fail and line.startswith("- "):
                first_detail = line[2:]
                break
        if first_detail.startswith("missing source comment lines"):
            for line in audit_result.stdout.splitlines():
                if line.startswith("- missing comment: "):
                    first_detail = f"{first_detail}; {line[2:]}"
                    break
        elif first_detail.startswith("heading sequence mismatch"):
            for line in audit_result.stdout.splitlines():
                if line.startswith("- heading mismatch "):
                    first_detail = f"{first_detail}; {line[2:]}"
                    break
        if not first_detail:
            for line in audit_result.stdout.splitlines():
                if line.startswith("- missing prose fragment line "):
                    first_detail = line[2:]
                    break
                if line.startswith("- ledger unresolved: "):
                    first_detail = line[2:]
                    break
                if line.startswith("- active Typst line: "):
                    first_detail = line[2:]
                    break
        detail = f" First unresolved audit item: {first_detail}." if first_detail else ""
        print(f"AUDIT_FAIL: build skipped.{detail} Repair the failed conversion pass; only STOP if that source span has no mechanical TeX conversion.", file=sys.stderr)
        return audit_result.returncode

    build_cmd = args.build_cmd
    if build_cmd and build_cmd[0] == "--":
        build_cmd = build_cmd[1:]
    if not build_cmd:
        print("audit PASS; no build command supplied")
        return 0

    return subprocess.run(build_cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
