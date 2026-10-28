import json
import os
import math
from scipy.stats import qmc
import argparse
import csv

PARAMS=["L","t","Bi"]

def load_config(path):
    with open(path)as f:
        return json.load(f)
    

def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
    return value




#return n samples as a list of rows: sample_id, L, t, Bi.
def draw_samples(config,n):
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    params=config["parameters"]
    # bounds of each parameter
    lows,highs=[],[]
    for name in PARAMS:
        p=params[name]
        if p["scale"]=="log":
            lows.append(math.log10(p["min"]))
            highs.append(math.log10(p["max"]))
        else:
            lows.append(p["min"])
            highs.append(p["max"])
    
    sampler =qmc.LatinHypercube(d=len(PARAMS), rng=config["sampling"]["seed"])
    unit_points = sampler.random(n)    # n points in the unit cube [0,1)
    points= qmc.scale(unit_points,lows, highs) #stretched to the real bounds
    
    rows = []
    for i, point in enumerate(points):
        row = {"sample_id": f"s{i:04d}"}  #stable ID: s0000, s0001,...
        for name, value in zip(PARAMS,point):
            if params[name]["scale"] == "log":
                value = 10 ** value   
            row[name] = round(float(value),6)
        rows.append(row)
    return rows


def main():

    parser = argparse.ArgumentParser(description="Draw the seeded (L,t,Bi) design.")
    parser.add_argument("--config", default="config/campaign.json", help="campaign configuration")
    parser.add_argument("--n", type=positive_int, required=True, help="number of samples")
    parser.add_argument("--output", default="data/samples.csv",help="output CSV")
    args = parser.parse_args()
    
    rows=draw_samples(load_config(args.config), args.n)
    
    # "sample.csv" has no directory part: dirname is "", so there is nothing to create
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    with open(args.output,"w",newline="") as f:
        writer=csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} samples to {args.output}")
    

if __name__=="__main__":
    main()
    
    