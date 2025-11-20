import os
import shutil
import subprocess
from typing import Dict, Optional
from valrep.modifiers import evaluate_formula

class MadGraphStep:
    """
    MadGraph execution step.

    :class attribute name: Step name used in workflow
    :class attribute execution_mode: Defines step iteration mode
    """
    name = "madgraph"
    execution_mode = "for_each"

    def __init__(self, config: Optional[Dict] = None, skip_if_done: bool = True, run_name: str = "run_01", **kwargs):
        """
        Initialize MadGraph step.

        :param config: Configuration dictionary for MG5 settings
        :param skip_if_done: Skip if outputs already exist
        :param run_name: Event generation tag
        :param kwargs: Extra arguments forwarded by StepManager
        """
        self.config = config or kwargs or {}
        self.skip_if_done = skip_if_done
        self.run_name = run_name

    def is_done(self, point_dir: str) -> bool:
        """
        Check if event generation output already exists.

        :param point_dir: Directory for model point
        :return: True if any expected event file exists
        """
        step_dir = os.path.join(point_dir, self.name)
        all_points_dir = os.path.abspath(os.path.join(point_dir, ".."))
        mass_name = os.path.basename(point_dir)

        # Candidate output files
        candidates = [
            os.path.join(step_dir, "Events", self.run_name, "unweighted_events.lhe.gz"),
            os.path.join(all_points_dir, "mg5_events_lhe", f"{mass_name}.lhe.gz"),
            os.path.join(all_points_dir, "mg5py8_events_hepmc", f"{mass_name}.hepmc.gz"),
        ]

        # Check size and existence
        for file_path in candidates:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                return True
        return False

    def run(self, config: Dict, point_dir: str, prev_output: Optional[str] = None) -> str:
        """
        Run MG5, edit cards, generate events, run Pythia8, and store outputs.

        :param config: Full workflow configuration
        :param point_dir: Point directory path
        :param prev_output: Previous SLHA or other input for MG5
        :return: Path to produced LHE or HEPMC file
        """
        print(f"[{self.name}] Starting: {point_dir}")
        step_dir = os.path.join(point_dir, self.name)
        os.makedirs(step_dir, exist_ok=True)

        # Output directories
        all_points_dir = os.path.abspath(os.path.join(point_dir, ".."))
        mass_name = os.path.basename(point_dir)
        lhe_out = os.path.join(all_points_dir, "mg5_events_lhe", f"{mass_name}.lhe.gz")
        hepmc_out = os.path.join(all_points_dir, "mg5py8_events_hepmc", f"{mass_name}.hepmc.gz")
        os.makedirs(os.path.dirname(lhe_out), exist_ok=True)
        os.makedirs(os.path.dirname(hepmc_out), exist_ok=True)

        # Skip if outputs already exist
        if self.skip_if_done and self.is_done(point_dir):
            print(f"[{self.name}] Existing output found, skipping.")
            if os.path.exists(hepmc_out):
                return hepmc_out
            elif os.path.exists(lhe_out):
                return lhe_out
            else:
                return ""

        # MG5 executable
        mg_exec = os.environ.get("MG5_EXEC")
        if mg_exec is None:
            raise FileNotFoundError("MG5_EXEC environment variable not set!")

        # MG5 config
        step_cfg = self.config.get("madgraph", self.config)
        proc_card_path = step_cfg["proc_card"]
        mg_dir = os.path.dirname(mg_exec)

        # Rewrite proc card with output directory
        new_proc_card = os.path.join(step_dir, os.path.basename(proc_card_path))
        with open(proc_card_path, "r") as f_in, open(new_proc_card, "w") as f_out:
            lines = f_in.readlines()
            for line in lines:
                if line.strip().startswith("output"):
                    f_out.write(f"output {step_dir}\n")
                else:
                    f_out.write(line)
            if not any(l.strip().startswith("output") for l in lines):
                f_out.write(f"output {step_dir}\n")

        # Launch MG5
        print(f"[{self.name}] Launching MG5...")
        log_file_path = os.path.join(point_dir, f"{self.name}_full.log")
        with open(log_file_path, "w") as log_file:
            proc = subprocess.Popen(
                [mg_exec, "-f", os.path.abspath(new_proc_card)],
                cwd=mg_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in proc.stdout:
                log_file.write(line)
                if line.startswith("INFO"):
                    print(line, end="")
            proc.wait()

        # MG5 status check
        if proc.returncode != 0:
            raise RuntimeError(f"[{self.name}] MG5 failed (log: {log_file_path})")

        print(f"[{self.name}] MG5 completed successfully.")

        # Build edit_cards script
        run_settings = step_cfg.get("run_settings", {})
        param_space = config.get("parameter_space", {})
        edit_script = os.path.join(step_dir, "edit_cards.mg5")

        with open(edit_script, "w") as f:
            f.write("edit_cards\n")
            f.write("shower = OFF\n")
            f.write("detector = OFF\n")
            f.write("analysis = OFF\n")
            f.write("madspin = OFF\n")
            f.write("reweight = OFF\n")
            f.write("done\n")

            # Use previous SLHA if provided
            if prev_output:
                f.write(f"{prev_output}\n")
                f.write("update to_slha2\n")
                f.write("update missing\n")

            # Set run_card parameters
            for key, val in run_settings.items():
                evaluated = evaluate_formula(val, param_space)
                if evaluated is None:
                    print(f"[{self.name}] Warning: could not evaluate {key} = {val}")
                    continue

                # Format numbers safely
                evaluated_str = (
                    str(int(evaluated)) if isinstance(evaluated, (int, float)) and float(evaluated).is_integer()
                    else f"{evaluated:.6g}" if isinstance(evaluated, float)
                    else str(evaluated)
                )
                f.write(f"set run_card {key} {evaluated_str}\n")
            f.write("done\n")

        # Madevent binary
        madevent_exec = os.path.join(step_dir, "bin", "madevent")
        if not os.path.exists(madevent_exec):
            raise FileNotFoundError(f"Madevent not found: {madevent_exec}")

        # Edit cards
        print(f"[{self.name}] Running Madevent edit_cards...")
        subprocess.run([madevent_exec, edit_script], cwd=step_dir, check=True)

        # Generate events
        gen_script = os.path.join(step_dir, "generate_events_script.mg5")
        with open(gen_script, "w") as f:
            f.write("generate_events -f\n")
        subprocess.run([madevent_exec, gen_script], cwd=step_dir, check=True)

        # Pythia8 script
        pythia8_settings = step_cfg.get("pythia8_settings", {})
        pythia_script = os.path.join(step_dir, "run_pythia8.mg5")
        with open(pythia_script, "w") as f:
            f.write(f"pythia8 --tag={self.run_name}\n")
            f.write("pythia8\n")
            for key, val in pythia8_settings.items():
                f.write(f"set {key} {val}\n")
            f.write("done\n")
        subprocess.run([madevent_exec, pythia_script], cwd=step_dir, check=True)

        # Collect outputs
        events_dir = os.path.join(step_dir, "Events", self.run_name)
        lhe_gz = os.path.join(events_dir, "unweighted_events.lhe.gz")
        hepmc_gz = os.path.join(events_dir, f"{self.run_name}_pythia8_events.hepmc.gz")

        if os.path.exists(lhe_gz):
            shutil.copy(lhe_gz, lhe_out)
        if os.path.exists(hepmc_gz):
            shutil.copy(hepmc_gz, hepmc_out)

        # Return available file
        if os.path.exists(hepmc_out):
            return hepmc_out
#        elif os.path.exists(lhe_out):
#            return lhe_out
        else:
            raise FileNotFoundError("MG5 did not produce any output files.")
