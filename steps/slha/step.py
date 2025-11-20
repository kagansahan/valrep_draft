import os
import shutil

class SLHAStep:
    name = "slha"
    execution_mode = "for_each"

    def __init__(self, slha_template=None, skip_if_done=True):
        """
        Initialize SLHA step.

        :param slha_template: Path to SLHA template
        :param skip_if_done: Skip if file exists
        """
        self.slha_template = slha_template
        self.skip_if_done = skip_if_done

    def is_done(self, point_dir):
        """
        Check if SLHA file already exists.

        :param point_dir: Directory for this parameter point
        :return: True if file exists and non-empty
        """
        slha_file = os.path.join(point_dir, self.name, "param_card.slha")
        return os.path.exists(slha_file) and os.path.getsize(slha_file) > 0

    def run(self, config, point_dir, prev_output=None):
        """
        Generate SLHA file and copy to results.

        :param config: Workflow configuration dict
        :param point_dir: Directory for this parameter point
        :param prev_output: Not used for SLHA
        :return: Path to generated SLHA file
        """
        step_dir = os.path.join(point_dir, self.name)
        os.makedirs(step_dir, exist_ok=True)

        slha_file = os.path.join(step_dir, "param_card.slha")

        # Get parameter space
        param_space = config.get("parameter_space", {})

        if self.skip_if_done and self.is_done(point_dir):
            print(f"[{self.name}] SLHA file exists, skipping.")
        else:
            # Read template
            with open(self.slha_template, "r") as f:
                lines = f.readlines()

            # Replace placeholders with values
            new_lines = []
            for line in lines:
                for pname, pinfo in param_space.items():
                    placeholder = f".{pname}."
                    if placeholder in line:
                        line = line.replace(placeholder, f"{float(pinfo['value']):.8E}")
                new_lines.append(line)

            # Write new SLHA
            with open(slha_file, "w") as f:
                f.writelines(new_lines)
            print(f"[{self.name}] Generated SLHA: {slha_file}")

        # Copy to results dir
        all_points_dir = config.get("workdir", "./all_points_runs")
        results_dir = os.path.join(all_points_dir, "slha_results")
        os.makedirs(results_dir, exist_ok=True)

        # Build dynamic filename
        topology = config.get("topology", "unknown")
        param_parts = [f"{pname}_{int(pinfo.get('value',0))}p0" for pname, pinfo in param_space.items()]
        new_filename = f"{topology}." + "_".join(param_parts) + ".slha"

        dest_path = os.path.join(results_dir, new_filename)
        shutil.copyfile(slha_file, dest_path)
        print(f"[{self.name}] Copied to: {dest_path}")

        return slha_file