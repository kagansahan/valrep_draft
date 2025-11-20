import os
import shutil
import subprocess
from typing import Dict, Optional

class CutLangStep:
    """
    Represents a CutLang analysis step in the ValRep workflow.

    Attributes
    ----------
    name : str
        Step identifier.
    execution_mode : str
        Indicates whether this step runs for each parameter point individually.
    """

    name = "cutlang"
    execution_mode = "for_each"

    def __init__(self, config: Optional[Dict] = None, skip_if_done: bool = True, **kwargs):
        """
        Initialize the CutLang step.

        Parameters
        ----------
        config : dict, optional
            Step-specific configuration dictionary.
        skip_if_done : bool, default True
            If True, the step will skip execution if output already exists.
        **kwargs
            Any additional parameters are stored in self.config.
        """
        self.config = config or kwargs or {}
        self.skip_if_done = skip_if_done

    def is_done(self, point_dir: str, adl_file: str) -> bool:
        """
        Check if CutLang output already exists for a given parameter point.

        Parameters
        ----------
        point_dir : str
            Directory corresponding to the current parameter point.
        adl_file : str
            Path to the CutLang ADL file.

        Returns
        -------
        bool
            True if the output ROOT file exists and is non-empty.
        """
        adl_basename = os.path.splitext(os.path.basename(adl_file))[0]
        output_root = os.path.join(point_dir, self.name, f"histoOut-{adl_basename}.root")
        return os.path.exists(output_root) and os.path.getsize(output_root) > 0

    def run(
        self,
        config: Optional[Dict] = None,
        point_dir: Optional[str] = None,
        prev_output: Optional[str] = None
    ) -> str:
        """
        Run CutLang for the given parameter point.

        Parameters
        ----------
        config : dict, optional
            Step configuration dictionary. If None, defaults to self.config.
        point_dir : str, optional
            Directory of the current parameter point.
        prev_output : str, optional
            Output from the previous step (required as input for CutLang).

        Returns
        -------
        str
            Path to the final ROOT output file stored under cutlang_results.

        Raises
        ------
        ValueError
            If prev_output is None.
        FileNotFoundError
            If CLA_EXEC environment variable is not set.
        """
        # Use provided config or default
        cfg = (self.config if config is None else config).get("cutlang", {})
        adl_file = cfg["adl_file"]
        adl_basename = os.path.splitext(os.path.basename(adl_file))[0]

        # Ensure step directory exists
        step_dir = os.path.join(point_dir, self.name)
        os.makedirs(step_dir, exist_ok=True)

        output_root = os.path.join(step_dir, f"histoOut-{adl_basename}.root")

        # Skip if output already exists
        if self.skip_if_done and self.is_done(point_dir, adl_file):
            print(f"[{self.name}] CutLang output exists, skipping.")
            return output_root

        if prev_output is None:
            raise ValueError(f"[{self.name}] prev_output is None. CutLang requires input from previous step!")

        # CutLang executable
        cla_exec = os.environ.get("CLA_EXEC")
        if cla_exec is None:
            raise FileNotFoundError("CLA_EXEC environment variable not set!")

        root_type = cfg.get("root_type", "DELPHES")

        # Run CutLang
        subprocess.run([cla_exec, prev_output, root_type, "-i", adl_file], cwd=step_dir, check=True)

        # Copy results to global cutlang_results directory
        all_points_dir = os.path.abspath(os.path.join(point_dir, ".."))
        cutlang_results_dir = os.path.join(all_points_dir, "cutlang_results")
        os.makedirs(cutlang_results_dir, exist_ok=True)

        mass_name = os.path.basename(point_dir)
        final_name = f"{mass_name}.root"
        final_path = os.path.join(cutlang_results_dir, final_name)

        shutil.copy(output_root, final_path)
        print(f"[{self.name}] Output copied to {final_path}")

        return final_path