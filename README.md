# valrep_draft

**valrep**: validation and reinterpretation workflow

> ⚠️ Draft version.

## Installation & Environment Setup

Before running the workflow, configure tool paths:
```bash
source setup_env.sh
```
The file defines environment variables:
* MG5_EXEC — MadGraph5 executable
* DELPHES_EXEC — DelphesHepMC2 executable
* CLA_EXEC — CutLang executable

Modify `setup_env.sh` to match your local installation.
## Running the Workflow

Use the CLI entry-point script to run the valrep:

```bash
python bin/valrep --config configs/full_workflow.yaml
```
### Options:

* Run a single step:
```bash
python bin/valrep --config configs/full_workflow.yaml  --step madgraph
```
* Run multiple steps (comma-separated):
```bash
python bin/valrep --config configs/full_workflow.yaml --steps slha,madgraph
```

* Specify output directory:
```bash 
python bin/valrep --config configs/full_workflow.yaml --workdir ./my_outputs
```
> ⚠️ Make sure all paths in the configuration file (slha_template, proc_card, delphes_card, adl_file) are updated to your local system before running.


## Requirements
* Python 3.10+
* MadGraph5_aMC@NLO (with mg5amc_py8_interface)
* Delphes3
* CutLang
