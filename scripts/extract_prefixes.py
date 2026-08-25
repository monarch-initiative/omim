import argparse
import re
from pathlib import Path


# Functional Syntax header uses lines like:
#   Prefix(obo:=<http://purl.obolibrary.org/obo/>)
PREFIX_RE = re.compile(r"^Prefix\(([^:]+):=<([^>]+)>\)\s*$", re.M)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract prefixes from OWL Functional Syntax header")
    parser.add_argument("--input", required=True, help="Path to .functional.owl file")
    parser.add_argument("--output", required=True, help="Path to output prefixes.csv")
    args = parser.parse_args()

    text = Path(args.input).read_text()
    rows = []
    for m in PREFIX_RE.finditer(text):
        prefix = m.group(1).strip()
        base = m.group(2).strip()
        rows.append((prefix, base))

    # Stabilize output for reproducible builds.
    rows = sorted(set(rows))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("prefix,base\n" + "\n".join([f"{p},{b}" for p, b in rows]) + "\n")
    print(f"Wrote {out} with {len(rows)} prefixes")


if __name__ == "__main__":
    main()
