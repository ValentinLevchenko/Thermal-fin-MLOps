import gmsh
import math, tempfile, itertools, os, subprocess, sys,csv

# Generate the 3D four fin case at each (L,t) corner and check
# markers, volume and mesh quality.

EXPECTED = {"Post", "Fin_1", "Fin_2","Fin_3","Fin_4","Gamma_root","Gamma_ext"}
GENERATOR="make_fins.py" #script that writes fin.geo 
L_VALUES=[0.5,0.2] #length
T_VALUES=[0.05,0.2] #thickness
H=0.1 #mesh size
D=0.75 #fixed fin spacing
OUT="domain-corners.csv" #results file

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
    
    gmsh.option.setNumber("Mesh.MeshSizeMax",H) #sets the largest allowed peice to H
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints",0) #ignore other sizes written inside the .geo
    gmsh.model.mesh.generate(3) #builds the 3D mesh
    
    #list of all the tetrahedra
    tets,_=gmsh.model.mesh.getElementsByType(4)
    
    quality=gmsh.model.mesh.getElementQualities(tets,"gamma")
    
    return {"L":L, "t":t, "h":H, "group_ok":EXPECTED.issubset(groups),
            "root_ok": root_ok, "volume_ok": math.isclose(volume, expected, rel_tol=1e-6),
            "n_tets":len(tets), "min_gamma":round(float(min(quality)),4)}
    
    

gmsh.initialize()
gmsh.option.setNumber("General.Terminal",0)
rows=[]
with tempfile.TemporaryDirectory() as tmp:
    for L,t in itertools.product(L_values, T_values):
        odir=os.path.join(tmp,f"L{L}_t{t}")
        subprocess.run([sys.executable, GENERATOR,"--dim", "3", "--N", "4", "--L", str(L),
                        "--t", str(t), "--d", str(D), "--cylinder", "0", "--odir", odir], check=True)
        
        rows.append(check(os.path.join(odir,"fin.geo"),L,t))
        print(rows[-1])
gmsh.finalize()

with open(OUT,"w",newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    

