#!/bin/bash
# ----------------------------------------
# setup_env.sh
# Sets environment variables required for
# the ValRep workflow pipeline.
#
# This script exports the paths to external
# tools such as MadGraph5, Delphes, and CutLang.
# ----------------------------------------

# Path to MadGraph5 executable
export MG5_EXEC="/path/to/mg5_aMC"

# Path to Delphes executable
export DELPHES_EXEC="/path/to/DelphesHepMC2"

# Path to CutLang launcher script
export CLA_EXEC="/path/to/CutLang/runs/CLA.sh"

# Optional: Additional tools may be added here
# export OTHER_EXEC="/path/to/other/tool"

# Display summary of exported variables
echo "Environment variables set:"
echo "MG5_EXEC = $MG5_EXEC"
echo "DELPHES_EXEC = $DELPHES_EXEC"
echo "CLA_EXEC = $CLA_EXEC"
