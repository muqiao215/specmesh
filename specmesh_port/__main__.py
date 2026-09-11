import argparse
import json
import sys
from .service import SpecMeshService


def main(argv=None):
    parser=argparse.ArgumentParser(description="Independent, read-only SpecMesh machine-profile proposal")
    parser.add_argument("--allowed-root",action="append",required=True)
    args=parser.parse_args(argv)
    try:
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
