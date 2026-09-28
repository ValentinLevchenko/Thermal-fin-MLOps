import gmsh
import math, tempfile, itertools, os, subprocess, sys,csv

# Generate the 3D four fin case at each (L,t) corner and check
# markers, volume and mesh quality.

EXPECTED = {"Post", "Fin_1", "Fin_2","Fin_3","Fin_4","Gamma_root","Gamma_ext"}
GENERATOR = "../feelpp/toolboxes/generator/cases/thermal_fin/case_generator_thermal_fin.py"
GENERATOR_COMMIT = "44487393868854b53e47e82217d3a0fbc557c8d1"

L_VALUES=[0.5,1,2.5] #length: min, reference, max
T_VALUES=[0.2,0.25,0.5] #thickness
H=0.1 #mesh size
D=0.75 #fixed fin spacing
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
    
def check_generator_commit():
    feelpp_dir=GENERATOR.split("/toolboxes/")[0] #"../feelpp"
    actual=subprocess.run(["git","-C",feelpp_dir, "rev-parse", "HEAD"],
                          capture_output= True,text=True,check=True).stdout.strip()
    if actual != GENERATOR_COMMIT:
        sys.exit(f"Feel++ checkout is on {actual}, expected pinned commit {GENERATOR_COMMIT}")
    




def main():
    check_generator_commit()
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal",0)
    rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        for L,t in itertools.product(L_VALUES, T_VALUES):
            odir=os.path.join(tmp,f"L{L}_t{t}")
            subprocess.run([sys.executable, GENERATOR,"--dim", "3", "--N", "4", "--L", str(L),
                            "--t", str(t), "--d", str(D), "--cylinder", "0", "--odir", odir], check=True)
            
            rows.append(check(os.path.join(odir,"fin.geo"),L,t,H))
            print(rows[-1])
    gmsh.finalize()
    
    

    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__=="__main__":
    main()

