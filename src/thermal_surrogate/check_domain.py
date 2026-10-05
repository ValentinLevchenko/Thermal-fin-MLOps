import gmsh
import math, tempfile, itertools, os, subprocess, sys,csv
import argparse # reading command-line arguments

# Path to the pinned Feel++ generator
DEFAULT_GENERATOR = os.environ.get( "FEELPP_THERMAL_FIN_GENERATOR",
    "../feelpp/toolboxes/generator/cases/thermal_fin/case_generator_thermal_fin.py")

# Generate the 3D four fin case at each (L,t) corner and check
# markers, volume and mesh quality.

EXPECTED = {"Post", "Fin_1", "Fin_2","Fin_3","Fin_4","Gamma_root","Gamma_ext"}
GENERATOR_COMMIT = "44487393868854b53e47e82217d3a0fbc557c8d1"

L_VALUES=[0.5,1,2.5] #length: min, reference, max
T_VALUES=[0.2,0.25,0.5] #thickness
H=0.1 #mesh size
D=0.75 #fixed fin spacing

# Gamma = 1 for a regular tetrahedron and tends to 0 for a flat "sliver" element.
# 0.1 is used as a sliver detector: unresolved thin fins (t < 2h) give min_gamma <= 0.013,
# while every resolved case gives min_gamma >= 0.12 (docs/evidence/t-lower-bound.csv),
# so any threshold in that gap gives the same decision. It is not a quality target:
# Gmsh's own optimizer works on elements below 0.3 (Mesh.OptimizeThreshold default). 
MIN_GAMMA=0.1
OUT = "docs/evidence/domain-corners.csv" #results file

# open .geo file, check its groups, root surface and volume, mesh it and return a result row
def check(geo, L,t,h):
    gmsh.clear()
    gmsh.onelab.clear() # fin.geo uses DefineNumber without this, Gmesh reuses the first case's L and t
    gmsh.open(geo)
    
    # map each physical group name to the list of entity tags it contains:
    groups ={}
    for dim, tag in gmsh.model.getPhysicalGroups():
        groups[gmsh.model.getPhysicalName(dim,tag)]=gmsh.model.getEntitiesForPhysicalGroup(dim,tag)
        
    # root is a single flat surface at z=0 with area 1
    root = groups.get("Gamma_root",[])
    root_ok=False
    if len(root) ==1:
        box=gmsh.model.getBoundingBox(2,root[0]) #(xmin, ymin, zmin, xmax, ymax, zmax)
        area = gmsh.model.occ.getMass(2,root[0])
        root_ok = (math.isclose(box[2], 0, abs_tol=1e-6) and math.isclose(box[5], 0, abs_tol=1e-6)
                and math.isclose(area, 1, abs_tol=1e-6))
        
    volume = sum(gmsh.model.occ.getMass(3,tag) for _,tag in gmsh.model.getEntities(3)) #get the volume bcz getEntities lists every solid piece
    expected=(4*(D+t)+t)+4*t*((2*L+1)**2-1) # compute the real value of the volume
    
    gmsh.option.setNumber("Mesh.MeshSizeMax",h) #sets the largest allowed peice to H
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints",0) #ignore other sizes written inside the .geo
    gmsh.model.mesh.generate(3) #builds the 3D mesh
    
    #list of all the tetrahedra
    tets,_=gmsh.model.mesh.getElementsByType(4)
    
    quality=gmsh.model.mesh.getElementQualities(tets,"gamma")
    
    return {"L":L, "t":t, "h":h, "group_ok":EXPECTED.issubset(groups),
            "root_ok": root_ok, "volume_ok": math.isclose(volume, expected, rel_tol=1e-6),
            "n_tets":len(tets), "min_gamma":round(float(min(quality)),4),
            "mesh_ok":float(min(quality)) >=MIN_GAMMA}
    
def check_generator_commit(generator):
    feelpp_dir=generator.split("/toolboxes/")[0] #"../feelpp"
    actual=subprocess.run(["git","-C",feelpp_dir, "rev-parse", "HEAD"],
                          capture_output= True,text=True,check=True).stdout.strip()
    if actual != GENERATOR_COMMIT:
        sys.exit(f"Feel++ checkout is on {actual}, expected pinned commit {GENERATOR_COMMIT}")
    




def main():
    parser=argparse.ArgumentParser(description="Check (L,t) domain corners of the thermal-fin generator.")
    parser.add_argument("--generator", default=DEFAULT_GENERATOR, help="path to case_generator_thermal_fin.py (or set FEELPP_THERMAL_FIN_GENERATOR)")
    parser.add_argument("--L", type=float, nargs="+", default=L_VALUES,help="fin length values")
    parser.add_argument("--t", type=float, nargs="+", default=T_VALUES,help="fin thickness values")
    parser.add_argument("--h", type=float, default=H,help="maximum mesh size")
    parser.add_argument("--out", default=OUT,help="results file")
    args=parser.parse_args()
    
    if not os.path.isfile(args.generator):
        sys.exit(f"Generator not found at {args.generator}. Clone feelpp/feelpp next to this repo or pass --generator/ set FEELPP_THERMAL_FIN_GENERATOR")
    
    check_generator_commit(args.generator)
    
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal",0)
    rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        for L,t in itertools.product(args.L,args.t):
            odir=os.path.join(tmp,f"L{L}_t{t}")
            subprocess.run([sys.executable, args.generator,"--dim", "3", "--N", "4", "--L", str(L),
                            "--t", str(t), "--d", str(D), "--cylinder", "0", "--odir", odir], check=True)
            
            rows.append(check(os.path.join(odir,"fin.geo"),L,t,args.h))
            print(rows[-1])
    gmsh.finalize()
    
    

    os.makedirs(os.path.dirname(args.out),exist_ok=True)
    with open(args.out,"w",newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.out}")

if __name__=="__main__":
    main()

