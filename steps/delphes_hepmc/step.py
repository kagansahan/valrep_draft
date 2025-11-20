import os
import gzip
import shutil
import subprocess
from typing import Dict, Optional

class DelphesHEPMCStep:
    """
    DelphesHepMC step for the valrep.

    This step runs Delphes on a gzip-compressed hepmc file, producing
    a ROOT output file. Each parameter point is processed separately.

    Attributes
    ----------
    name : str
        Step name identifier.
    config : dict
        Step-specific configuration.
    skip_if_done : bool
        If True, skip execution if output already exists.
    """
    name = "delphes_hepmc"
    execution_mode = "for_each"

    def __init__(self, config: Optional[Dict] = None, skip_if_done: bool = True, **kwargs):
        """
        Initialize DelphesHEPMCStep.

        Parameters
        ----------
        config : dict, optional
            Step-specific configuration dictionary.
        skip_if_done : bool, default=True
            Skip this step if output already exists.
        kwargs : dict
            Additional unused parameters.
        """
        self.config = config or kwargs or {}
        self.skip_if_done = skip_if_done

    def is_done(self, point_dir: str) -> bool:
        """
        Check if the ROOT output already exists.

        Parameters
        ----------
        point_dir : str
            Directory of the current parameter point.

        Returns
        -------
        bool
            True if output exists and is non-empty, False otherwise.
        """
        output_root = os.path.join(point_dir, self.name, "delphes_output.root")
        return os.path.exists(output_root) and os.path.getsize(output_root) > 0

    def run(
        self,
        config: Optional[Dict] = None,
        point_dir: Optional[str] = None,
        prev_output: Optional[str] = None
    ) -> str:
        """
        Run Delphes simulation for one parameter point.

        Parameters
        ----------
        config : dict, optional
            Workflow configuration (defaults to self.config).
        point_dir : str
            Directory of the current parameter point.
        prev_output : str
            Path to the gzip-compressed HEPMC input file.

        Returns
        -------
        str
            Path to the generated ROOT output file.

        Raises
        ------
        ValueError
            If point_dir or prev_output is invalid.
        FileNotFoundError
            If DELPHES_EXEC environment variable is not set.
        """
        if point_dir is None:
            raise ValueError(f"[{self.name}] point_dir cannot be None!")

        step_dir = os.path.join(point_dir, self.name)
        os.makedirs(step_dir, exist_ok=True)

        output_root = os.path.join(step_dir, "delphes_output.root")
        if self.skip_if_done and self.is_done(point_dir):
            print(f"[{self.name}] Output already exists, skipping.")
            return output_root

        delphes_exec = os.environ.get("DELPHES_EXEC")
        if delphes_exec is None:
            raise FileNotFoundError(f"[{self.name}] DELPHES_EXEC not set!")

        step_cfg = (config or self.config).get("delphes", {})
        delphes_card = step_cfg.get("card_path")
        if delphes_card is None:
            raise ValueError(f"[{self.name}] 'card_path' missing in config: {step_cfg}")

        if prev_output is None or not os.path.exists(prev_output):
            raise ValueError(f"[{self.name}] Invalid prev_output: {prev_output}")

        # Unpack gzip HEPMC to temporary file
        tmp_hepmc = os.path.join(step_dir, "input.hepmc")
        with gzip.open(prev_output, "rb") as f_in, open(tmp_hepmc, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        # Run Delphes
        print(f"[{self.name}] Running Delphes: {tmp_hepmc} -> {output_root}")
        subprocess.run([delphes_exec, delphes_card, output_root, tmp_hepmc], cwd=step_dir, check=True)

        # Clean up temporary HEPMC
        os.remove(tmp_hepmc)

        return output_root
