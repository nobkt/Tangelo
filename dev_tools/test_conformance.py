import unittest
from pathlib import Path
import pycodestyle


class TestCodeFormat(unittest.TestCase):

    def test_conformance(self):
        # Resolve paths relative to repository root
        repo_root = Path(__file__).resolve().parent.parent
        pkg_dir = repo_root / "tangelo"
        config_file = repo_root / "dev_tools" / "pycodestyle"

        # Defensive assertions
        assert pkg_dir.exists(), f"Package directory not found: {pkg_dir}"
        assert config_file.exists(), f"Config file not found: {config_file}"

        style = pycodestyle.StyleGuide(quiet=False, config_file=str(config_file))
        result = style.check_files([str(pkg_dir)])
        self.assertEqual(result.total_errors, 0, "Found code style errors and warnings.")


if __name__ == "__main__":
    unittest.main()
