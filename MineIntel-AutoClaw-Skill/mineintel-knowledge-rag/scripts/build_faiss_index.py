#!/usr/bin/env python3
"""Build the MineIntel semantic FAISS index."""

from __future__ import annotations

import json
import sys

from faiss_store import InfrastructureError, build_index


def main() -> int:
    try:
        manifest = build_index()
    except InfrastructureError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"status": "success", "index": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
