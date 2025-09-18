import json
from typing import Any


class OutputFormatter:
    """Handles formatting of dependency resolution results."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def format_json(self, dependencies: dict[str, Any], pretty_print: bool = True) -> str:
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

    def create_excerpt(self, dependencies: dict[str, Any], max_deps_per_section: int = 3) -> dict[str, Any]:
        """Create an excerpt of dependencies for debug mode."""
        excerpt: dict[str, Any] = {}

        for section_name, section_data in dependencies.items():
            if section_name.startswith("_"):
                # Copy container info and other metadata as-is
                excerpt[section_name] = section_data
            elif section_name in ("project", "system"):
                # Handle new unified structure with packages array
                excerpt[section_name] = {}

                for key, value in section_data.items():
                    if key != "packages":
                        # Copy metadata (package-management and other metadata)
                        excerpt[section_name][key] = value

                if "packages" in section_data:
                    packages = section_data["packages"]
                    total_packages = len(packages)

                    if total_packages <= max_deps_per_section:
                        excerpt[section_name]["packages"] = packages
                    else:
                        limited_packages = packages[:max_deps_per_section]
                        excerpt[section_name]["packages"] = limited_packages
                        excerpt[section_name]["_excerpt_info"] = {
                            "total_packages": total_packages,
                            "shown": max_deps_per_section,
                            "note": f"Showing {max_deps_per_section} of {total_packages} packages (debug mode excerpt)",
                        }
            else:
                # Fallback for any legacy structure
                excerpt[section_name] = section_data

        return excerpt
