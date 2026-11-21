"""File discovery module for finding relevant files for implementation tasks."""

import fnmatch
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FileDiscovery:
    """Discovers and categorizes files relevant to implementation tasks."""

    # Common patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        "*.pyc",
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".env",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
        "*.log",
    ]

    def __init__(
        self,
        root_path: Path,
        ignore_patterns: Optional[List[str]] = None
    ):
        """
        Initialize file discovery.

        Args:
            root_path: Root directory to search from
            ignore_patterns: Additional patterns to ignore
        """
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        if ignore_patterns:
            self.ignore_patterns.extend(ignore_patterns)

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        name = path.name
        rel_path = str(path.relative_to(self.root_path))

        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False

    def find_by_extension(self, extensions: List[str]) -> List[Path]:
        """
        Find all files with given extensions.

        Args:
            extensions: List of extensions (e.g., [".py", ".js"])

        Returns:
            List of matching file paths
        """
        results = []

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Filter directories to ignore
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]

            for file in files:
                file_path = root_path / file
                if self._should_ignore(file_path):
                    continue

                if any(file.endswith(ext) for ext in extensions):
                    results.append(file_path)

        return sorted(results)

    def find_by_name_pattern(self, pattern: str) -> List[Path]:
        """
        Find files matching a name pattern.

        Args:
            pattern: Glob pattern for file names (e.g., "test_*.py")

        Returns:
            List of matching file paths
        """
        results = []

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]

            for file in files:
                file_path = root_path / file
                if self._should_ignore(file_path):
                    continue

                if fnmatch.fnmatch(file, pattern):
                    results.append(file_path)

        return sorted(results)

    def find_by_content(
        self,
        search_pattern: str,
        extensions: Optional[List[str]] = None,
        regex: bool = False
    ) -> List[Tuple[Path, List[int]]]:
        """
        Find files containing specific content.

        Args:
            search_pattern: String or regex pattern to search for
            extensions: Limit search to these extensions
            regex: Whether to treat pattern as regex

        Returns:
            List of (file_path, matching_line_numbers) tuples
        """
        results = []

        if regex:
            pattern = re.compile(search_pattern)

            def match_func(line: str) -> bool:
                return bool(pattern.search(line))
        else:

            def match_func(line: str) -> bool:
                return search_pattern in line

        files_to_search = self.find_by_extension(extensions) if extensions else self._all_files()

        for file_path in files_to_search:
            try:
                matching_lines = []
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if match_func(line):
                            matching_lines.append(i)

                if matching_lines:
                    results.append((file_path, matching_lines))
            except Exception:
                continue

        return results

    def _all_files(self) -> List[Path]:
        """Get all non-ignored files."""
        results = []

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]

            for file in files:
                file_path = root_path / file
                if not self._should_ignore(file_path):
                    results.append(file_path)

        return results

    def find_related_files(
        self,
        file_path: Path,
        include_tests: bool = True,
        include_imports: bool = True
    ) -> Dict[str, List[Path]]:
        """
        Find files related to a given file.

        Args:
            file_path: The file to find related files for
            include_tests: Include test files
            include_imports: Include files that import/are imported by this file

        Returns:
            Dictionary with categories of related files
        """
        results: Dict[str, List[Path]] = {
            "tests": [],
            "imports": [],
            "imported_by": [],
            "same_directory": [],
        }

        file_path = Path(file_path).resolve()
        if not file_path.exists():
            return results

        file_name = file_path.stem
        file_ext = file_path.suffix
        file_dir = file_path.parent

        # Find test files
        if include_tests and not file_name.startswith("test_"):
            test_patterns = [
                f"test_{file_name}{file_ext}",
                f"{file_name}_test{file_ext}",
                f"tests/test_{file_name}{file_ext}",
            ]
            for pattern in test_patterns:
                for test_file in self.find_by_name_pattern(f"*{pattern}"):
                    if test_file not in results["tests"]:
                        results["tests"].append(test_file)

        # Find files in same directory
        if file_dir.exists():
            for sibling in file_dir.iterdir():
                if sibling.is_file() and sibling != file_path and sibling.suffix == file_ext:
                    if not self._should_ignore(sibling):
                        results["same_directory"].append(sibling)

        # Find import relationships (Python-specific)
        if include_imports and file_ext == ".py":
            module_name = file_name

            # Files that import this file
            import_pattern = rf"(?:from|import)\s+.*{re.escape(module_name)}"
            for found_file, _ in self.find_by_content(import_pattern, [".py"], regex=True):
                if found_file != file_path:
                    results["imported_by"].append(found_file)

            # Files imported by this file
            try:
                content = file_path.read_text(encoding="utf-8")
                import_matches = re.findall(
                    r'(?:from\s+(\S+)\s+import|import\s+(\S+))',
                    content
                )
                for match in import_matches:
                    module = match[0] or match[1]
                    module_parts = module.split(".")
                    for search_path in self.find_by_name_pattern(f"{module_parts[-1]}.py"):
                        if search_path not in results["imports"]:
                            results["imports"].append(search_path)
            except Exception:
                pass

        return results

    def get_project_structure(
        self,
        max_depth: int = 3
    ) -> Dict[str, any]:
        """
        Get a summary of the project structure.

        Args:
            max_depth: Maximum directory depth to explore

        Returns:
            Dictionary describing project structure
        """
        structure = {
            "root": str(self.root_path),
            "directories": [],
            "file_counts": {},
            "total_files": 0,
        }

        extension_counts: Dict[str, int] = {}

        def explore(path: Path, depth: int) -> Optional[Dict]:
            if depth > max_depth:
                return None
            if self._should_ignore(path):
                return None

            if path.is_file():
                ext = path.suffix or "no_extension"
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
                structure["total_files"] += 1
                return None

            dir_info = {
                "name": path.name,
                "path": str(path.relative_to(self.root_path)),
                "subdirs": [],
            }

            try:
                for child in sorted(path.iterdir()):
                    if child.is_dir() and not self._should_ignore(child):
                        subdir = explore(child, depth + 1)
                        if subdir:
                            dir_info["subdirs"].append(subdir)
                    elif child.is_file():
                        explore(child, depth)
            except PermissionError:
                pass

            return dir_info

        root_info = explore(self.root_path, 0)
        if root_info:
            structure["directories"] = root_info.get("subdirs", [])

        structure["file_counts"] = extension_counts

        return structure


def discover_implementation_context(
    root_path: Path,
    task_description: str
) -> Dict[str, List[Path]]:
    """
    Discover files relevant to an implementation task.

    Args:
        root_path: Project root
        task_description: Description of the task

    Returns:
        Dictionary with categorized relevant files
    """
    discovery = FileDiscovery(root_path)

    # Extract potential file/module names from description
    name_patterns = re.findall(r'[`"]([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)?)[`"]', task_description)

    results = {
        "mentioned_files": [],
        "related_python": [],
        "related_tests": [],
        "config_files": [],
    }

    # Find explicitly mentioned files
    for pattern in name_patterns:
        if "." in pattern:
            # Looks like a file
            matches = discovery.find_by_name_pattern(f"*{pattern}*")
            results["mentioned_files"].extend(matches)
        else:
            # Looks like a module/class name
            matches = discovery.find_by_content(pattern, [".py"])
            results["related_python"].extend([m[0] for m in matches])

    # Find config files
    config_patterns = ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini", "*.cfg"]
    for pattern in config_patterns:
        results["config_files"].extend(discovery.find_by_name_pattern(pattern))

    # Deduplicate
    for key in results:
        results[key] = list(set(results[key]))

    return results
