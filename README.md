# 2026-m2-thermalfin-grab-gb
M2 2026 3D thermal-fin MLOps project - Gradient Boosting

## Project structure

The repository follows the project architecture defined in the course specification:

- `config/` - campaign and training configuration
- `cases/template/` - templates for generated thermal-fin cases
- `src/thermal_surrogate/` - case generation, simulation workflow, dataset, training, prediction and validation code
- `slurm/` - Slurm job scripts for Gaya
- `containers/` - container definitions and related files
- `data/` - dataset documentation and generated data references
- `tests/` - automated tests and test fixtures
- `artifacts/` - generated models, predictions and other experiment outputs
- `docs/` - project documentation
- `.github/workflows/` - continuous integration

## Milestones

- [ ] Define the parameter domain and sampling plan
- [ ] Generate and validate the 3D cases
  - [ ] Generate the 3D four-fin geometry
  - [ ] Generate the heat configuration and measure the quantities of interest
  - [ ] Validate a reference case
  - [ ] Automate case generation and record provenance
- [ ] Run the Gaya simulation campaign
- [ ] Build and freeze the learning dataset
- [ ] Train and verify the Gradient Boosting surrogate
- [ ] Optimize and confirm the final design
- [ ] Prepare the English oral presentation

## Run instructions

### Set up the environment

Requires Python 3.11+ and `uv`.

```bash
uv sync
```

### Activate the project environment

```bash
source .venv/bin/activate
```

### Generate the reference geometry

```bash
python src/thermal_surrogate/prepare.py
```

### Generate the reference mesh 

```bash
gmsh work/reference/fin.geo
```