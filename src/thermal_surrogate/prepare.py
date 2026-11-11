import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from liquid import Environment, FileSystemLoader




ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR   = ROOT / "cases/template"
DEFAULT_OUTPUT = ROOT / "work/reference"


def file_hash(path):

    """Calculate SHA-256 hash of a file."""

    content = Path(path).read_bytes()

    return hashlib.sha256(content).hexdigest()


def generate_case(N, L, d, t, output_dir):

    """Generate geometry and Feel++ configuration files."""

    output_dir.mkdir(parents = True, exist_ok = True)

    env = Environment(loader = FileSystemLoader(str(TEMPLATE_DIR)))

    geo_template  = env.get_template("fin.geo.liquid")
    json_template = env.get_template("thermal_fin.json.liquid")
    cfg_template  = env.get_template("thermal-fin.cfg.liquid")

    geo = geo_template.render(
        N = N, L = L, d = d, t = t,
        PostShape = "Box", PostArgs = "{0, 0, 0, 1, 1, N * (d + t) + t}",
        FinShape = "Box", FinArgs = "{-L, -L, r * (d + t), 2 * L + 1, 2 * L + 1, t}",
        eltDim = "Volume", eltDimM1 = "Surface", step = 1, physicalArg = "{r}",
        diffVal = 5
    )

    physics = json_template.render(dim = 3, fins = list(range(1, N + 1)))
    config = cfg_template.render(dim = 3)

    physics_for_validation = "\n".join(
        line for line in physics.splitlines()
        if not line.strip().startswith("//")
    )

    json.loads(physics_for_validation)

    geo_path  = output_dir / "fin.geo"
    json_path = output_dir / "thermal-fin.json"
    cfg_path  = output_dir / "thermal-fin.cfg"

    geo_path.write_text(geo, encoding = "utf-8")
    json_path.write_text(physics_for_validation, encoding = "utf-8")
    cfg_path.write_text(config, encoding = "utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "N": N,
            "L": L,
            "d": d,
            "t": t
        },
        "geometry": {
            "dimension": 3,
            "shape": "boxes"
        },
        "files": {
            "fin.geo": file_hash(geo_path),
            "thermal-fin.json": file_hash(json_path),
            "thermal-fin.cfg": file_hash(cfg_path)
        },
        "templates": {
            "fin.geo.liquid": file_hash(TEMPLATE_DIR / "fin.geo.liquid"),
            "thermal_fin.json.liquid": file_hash(TEMPLATE_DIR / "thermal_fin.json.liquid"),
            "thermal-fin.cfg.liquid": file_hash(TEMPLATE_DIR / "thermal-fin.cfg.liquid")
        }
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent = 4), encoding = "utf-8")

    print(f"Case generated in: {output_dir}")
    print(f"Parameters: N = {N}, L = {L}, d = {d}, t = {t}")




def main():

    parser = argparse.ArgumentParser(description = "Generate a 3D thermal-fin case.")

    parser.add_argument("--N",      type = int,   default = 4)
    parser.add_argument("--L",      type = float, default = 2.5)
    parser.add_argument("--d",      type = float, default = 0.75)
    parser.add_argument("--t",      type = float, default = 0.25)
    parser.add_argument("--output", type = Path, default = DEFAULT_OUTPUT)

    args = parser.parse_args()

    if args.N <= 0:
        parser.error("N must be positive")
    if args.L <= 0:
        parser.error("L must be positive")
    if args.d <= 0:
        parser.error("d must be positive")
    if args.t <= 0:
        parser.error("t must be positive")

    generate_case(
        N = args.N, L = args.L, d = args.d, t = args.t,
        output_dir = args.output
    )




if __name__ == "__main__":

    main()