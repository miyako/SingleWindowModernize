"""Generate the static fictional Japanese customer fixture, never at 4D startup."""
import argparse
from pathlib import Path


TARGET = (Path(__file__).resolve().parents[1] / "demo" / "4D Invoice"
          / "Resources" / "ja.lproj" / "Clients.txt")


def customer_bytes():
    names = ("デモ文具", "デモ商事", "デモ印刷", "デモ企画")
    lines = []
    for index in range(1, 201):
        values = (
            f"{names[(index - 1) % len(names)]}{index:03}（架空）",
            f"見本町{(index - 1) // 20 + 1}丁目{(index - 1) % 20 + 1}番地",
            "サンプル市", "架空県", "0000000", "日本", "", "", "", "", "",
        )
        lines.append("\t".join(values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    args = parser.parse_args()
    content = customer_bytes()
    if TARGET.exists():
        if TARGET.read_bytes() != content:
            raise ValueError(f"Fixture differs; refusing to overwrite edits: {TARGET}")
    elif args.check:
        raise FileNotFoundError(TARGET)
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        with TARGET.open("xb") as stream:
            stream.write(content)
    print(f"200 static fictional customers: {TARGET}")


if __name__ == "__main__":
    main()
