import argparse
import json
import os
import sys
from .service import SpecMeshService
from .contracts_runtime import validate


def main(argv=None):
    parser=argparse.ArgumentParser(description="Independent, read-only SpecMesh machine-profile proposal")
    parser.add_argument("--allowed-root",action="append")
    parser.add_argument("--capabilities",action="store_true")
    args=parser.parse_args(argv)
    try:
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
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536: raise ValueError("request_too_large")
        result=SpecMeshService(args.allowed_root).check(json.loads(raw))
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result["status"]=="pass" else 3
    except Exception as exc:
        print(json.dumps({"error_type":type(exc).__name__,"error":"request_rejected"}),file=sys.stderr)
        return 2
if __name__ == "__main__":
    raise SystemExit(main())
