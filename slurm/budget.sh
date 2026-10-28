#!/bin/bash
#SBATCH --job-name=budget
#SBATCH --partition=public
#SBATCH --ntasks=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --array=0-2
#SBATCH --output=logs/budget-%A_%a.out
#SBATCH --error=logs/budget-%A_%a.err


# Timing run for the sample budget: mesh and solve the cheapest, reference
# and most expensive (L, t) corners, one array task per case, 1 MPI rank.
set -euo pipefail


APPTAINER=/opt/apptainer/v1.4.3/bin/apptainer
SIF=/data/cemosis/benchmark/feelpp-noble.sif
H_MAX=0.1

CASES=(L0.5_t0.2 L1_t0.25 L2.5_t0.5)
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
CASE_DIR=$HOME/M2/budget/$CASE
RESULTS=$HOME/M2/budget-results/${CASE}_job${SLURM_ARRAY_JOB_ID}


mkdir -p "$RESULTS"
cd "$CASE_DIR"
echo "case=$CASE job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} node=$(hostname) sif=$SIF"


# 1. Mesh. fin.geo sets its own sizes, so load it first and override them afterwards.
printf 'Merge "fin.geo";\nMesh.MeshSizeMax = %s;\nMesh.MeshSizeFromPoints = 0;\n' "$H_MAX" > mesh.geo
t0=$(date +%s)
"$APPTAINER" exec "$SIF" gmsh mesh.geo -3 -format msh2 -o fin.msh
t1=$(date +%s)


# 2. Solve the steady heat problem.
"$APPTAINER" exec "$SIF" feelpp_toolbox_heat --config-file thermal-fin.cfg --directory "$RESULTS"
t2=$(date +%s)

echo "mesh_seconds=$((t1 - t0)) solve_seconds=$((t2 - t1)) total_seconds=$((t2 - t0))"


