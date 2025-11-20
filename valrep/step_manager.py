import importlib.util
import os
from typing import Dict, Type, Optional

class StepManager:
    """
    Discover and manage workflow steps dynamically.

    This class scans a steps directory, imports step modules,
    and keeps a registry of step classes. Each step can then be
    instantiated via `get_step()`.

    Attributes
    ----------
    steps_dir : str
        Absolute path to the folder containing step subfolders.
    registry : dict[str, Type]
        Mapping from step name to step class.
    """

    def __init__(self, steps_dir: Optional[str] = None):
        """
        Initialize the manager and discover available steps.

        Parameters
        ----------
        steps_dir : str, optional
            Path to the steps folder. Defaults to "<project_root>/steps".
        """
        if steps_dir is None:
            steps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "steps"))
        self.steps_dir = steps_dir
        self.registry: Dict[str, Type] = {}

        # Automatically scan the steps folder and populate the registry
        self.discover_steps()

    def discover_steps(self):
        """
        Scan the steps directory and register all step classes.

        Each step should be in a subfolder and contain a `step.py` file
        with a single class representing the step.
        """
        for step_name in os.listdir(self.steps_dir):
            step_folder = os.path.join(self.steps_dir, step_name)
            step_file = os.path.join(step_folder, "step.py")

            # Only consider directories that contain step.py
            if os.path.isdir(step_folder) and os.path.isfile(step_file):
                spec = importlib.util.spec_from_file_location(f"{step_name}.step", step_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Pick the first class found in the module
                step_cls = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):
                        step_cls = attr
                        break

                if step_cls is None:
                    raise ValueError(f"No class found in {step_file}")

                # Register step with lowercase name for convenience
                self.registry[step_name.lower()] = step_cls

    def get_step(self, name: str, config: Optional[dict] = None):
        """
        Retrieve a step instance by name.

        Parameters
        ----------
        name : str
            Name of the step to instantiate (case-insensitive).
        config : dict, optional
            Configuration dictionary to pass to the step constructor.

        Returns
        -------
        instance
            An instance of the requested step class.

        Raises
        ------
        ValueError
            If the step name is not registered.
        TypeError
            If config is not a dictionary.
        """
        step_cls = self.registry.get(name.lower())
        if not step_cls:
            raise ValueError(f"Unknown step: {name}")

        # Ensure config is a dictionary
        if config is None:
            config = {}
        elif not isinstance(config, dict):
            raise TypeError(f"Config must be a dict, got {type(config)}")

        # Instantiate the step with the provided config
        return step_cls(**config)
