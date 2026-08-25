"""Check that every FastAPI REST route is represented in openapi.yaml.

The checked-in contract intentionally documents the stable path/method surface;
FastAPI remains authoritative for generated request and response schemas.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from app.main import app

contract = (Path(__file__).parents[2] / "openapi.yaml").read_text()
missing = []
contract_lines = contract.splitlines()
for route in app.routes:
    if not getattr(route, "methods", None) or route.path in {"/docs", "/docs/oauth2-redirect", "/redoc"} or route.path.startswith("/openapi"):
        continue
    matches=[i for i,line in enumerate(contract_lines) if re.match(rf"^\s{{2}}{re.escape(route.path)}:\s*$",line)]
    if not matches:
        missing.append(route.path)
        continue
    start=matches[0]+1
    end=next((i for i in range(start,len(contract_lines)) if re.match(r"^\s{2}/",contract_lines[i])),len(contract_lines))
    for method in route.methods:
        if not re.search(rf"^\s{{4}}{method.lower()}:","\n".join(contract_lines[start:end]),re.MULTILINE):
            raise SystemExit(f"Missing {method} operation for {route.path} in openapi.yaml")
if missing:
    raise SystemExit("Missing paths in openapi.yaml: " + ", ".join(sorted(set(missing))))
print(f"OpenAPI contract covers {len({r.path for r in app.routes if getattr(r, 'methods', None)})} FastAPI REST paths.")
