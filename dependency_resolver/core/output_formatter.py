import json
from typing import Dict, Any


class OutputFormatter:
    """Handles formatting of dependency resolution results."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def format_json(self, dependencies: Dict[str, Any], pretty_print: bool = True) -> str:
        """Format dependencies as JSON string."""
        if self.debug:
            excerpt = self.create_excerpt(dependencies)
            if pretty_print:
                return json.dumps(excerpt, indent=2)
            else:
                return json.dumps(excerpt)
        else:
            if pretty_print:
                return json.dumps(dependencies, indent=2)
            else:
                return json.dumps(dependencies)

    def create_excerpt(self, dependencies: Dict[str, Any], max_deps_per_manager: int = 3) -> Dict[str, Any]:
        """Create an excerpt of dependencies for debug mode."""
        excerpt: Dict[str, Any] = {}

        for manager_name, manager_data in dependencies.items():
            excerpt[manager_name] = {}

            for key, value in manager_data.items():
                if key != "dependencies":
                    excerpt[manager_name][key] = value

            if "dependencies" in manager_data:
                deps = manager_data["dependencies"]
                total_deps = len(deps)

                if total_deps <= max_deps_per_manager:
                    excerpt[manager_name]["dependencies"] = deps
                else:
                    limited_deps = dict(list(deps.items())[:max_deps_per_manager])
                    excerpt[manager_name]["dependencies"] = limited_deps
                    excerpt[manager_name]["_excerpt_info"] = {
                        "total_dependencies": total_deps,
                        "shown": max_deps_per_manager,
                        "note": f"Showing {max_deps_per_manager} of {total_deps} dependencies (debug mode excerpt)",
                    }

        return excerpt
