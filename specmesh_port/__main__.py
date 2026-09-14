import argparse
import json
import os
import sys
from pathlib import Path
from .service import SpecMeshService
from .contracts_runtime import validate
from .project_state import render_project_state
from .handoff import render_handoff


def main(argv=None):
    parser=argparse.ArgumentParser(description="Independent, read-only SpecMesh machine-profile proposal")
    parser.add_argument("--allowed-root",action="append")
    parser.add_argument("--capabilities",action="store_true")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--project-state",choices=("json", "text"))
    parser.add_argument("--handoff",choices=("json", "text"))
    parser.add_argument("--verify-handoff")
    parser.add_argument("--task-path", help="Trusted task selection required when verifying a handoff")
    parser.add_argument("--scope-path", action="append", default=[], help="Explicit additional file in the handoff scope")
    args=parser.parse_args(argv)
    try:
        if args.version:
            from . import __version__
            print(__version__)
            return 0
        if args.capabilities:
            if args.allowed_root:
                raise ValueError("capabilities_has_no_repository")
            result = {"contract_version": "specmesh.port.v1-draft", "profile_version": "specmesh.snapshot.v1",
                      "read_only": True, "supported": os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW"),
                      "snapshot": "revalidate_content_and_git", "closeout": "external_verification_required"}
            print(json.dumps(validate("specmesh-capabilities", result)))
            return 0
        if not args.allowed_root:
            raise ValueError("allowed_root_required")
        service=SpecMeshService(args.allowed_root)
        if args.verify_handoff:
            max_bytes = 1024 * 1024
            if args.verify_handoff == "-":
                raw_b = sys.stdin.buffer.read(max_bytes + 1)
                if len(raw_b) > max_bytes:
                    raise ValueError("handoff_payload_too_large")
                raw_h = raw_b.decode("utf-8")
            else:
                import stat
                fd = os.open(args.verify_handoff, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
                try:
                    before = os.fstat(fd)
                    if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                        raise ValueError("handoff_file_invalid_or_too_large")
                    with os.fdopen(os.dup(fd), "rb") as stream:
                        raw_b = stream.read(max_bytes + 1)
                    after = os.fstat(fd)
                    if (len(raw_b) > max_bytes or
                            (before.st_size, before.st_mtime_ns, before.st_ctime_ns) !=
                            (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                        raise ValueError("handoff_file_changed_or_too_large")
                    raw_h = raw_b.decode("utf-8")
                finally:
                    os.close(fd)
            h_data = json.loads(raw_h)
            v_res = service.verify_handoff(h_data, args.allowed_root[0], task_path=args.task_path, paths=args.scope_path)
            print(json.dumps(v_res, ensure_ascii=False))
            return 0 if v_res["executable"] else 3
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536: raise ValueError("request_too_large")
        request=json.loads(raw)
        if args.handoff:
            result=service.prepare_handoff(request, paths=args.scope_path)
            if args.handoff == "json":
                print(json.dumps(result,ensure_ascii=False))
            else:
                print(render_handoff(result),end="")
            return 0 if result["executable"] else 3
        if args.project_state:
            result=service.project_state(request)
            if args.project_state == "json":
                print(json.dumps(result,ensure_ascii=False))
            else:
                print(render_project_state(result),end="")
            return 0 if result["state"]=="observed" else 3
        result=service.check(request)
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result["status"]=="pass" else 3
    except Exception as exc:
        print(json.dumps({"error_type":type(exc).__name__,"error":"request_rejected"}),file=sys.stderr)
        return 2
if __name__ == "__main__":
    raise SystemExit(main())
