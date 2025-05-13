#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch
import codebase_merger

class TestCodebaseMerger(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        
        # Create some test files
        self.create_test_files()
    
    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()
    
    def create_test_files(self):
        # Create a simple directory structure with files
        base_dir = self.test_dir.name
        
        # Create directories
        os.makedirs(os.path.join(base_dir, "src", "main"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "src", "test"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, ".git"), exist_ok=True)  # Should be ignored
        
        # Create text files
        with open(os.path.join(base_dir, "README.md"), "w") as f:
            f.write("# Test Repository\nThis is a test repository.\n")
        
        with open(os.path.join(base_dir, "src", "main", "app.py"), "w") as f:
            f.write("def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()\n")
        
        with open(os.path.join(base_dir, "src", "test", "test_app.py"), "w") as f:
            f.write("import unittest\n\nclass TestApp(unittest.TestCase):\n    def test_main(self):\n        self.assertTrue(True)\n")
        
        # Create a binary file (should be ignored)
        with open(os.path.join(base_dir, "binary_file.bin"), "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04")
    
    def test_should_include_file(self):
        # Test text files
        self.assertTrue(codebase_merger.should_include_file(
            os.path.join(self.test_dir.name, "README.md")
        ))
        
        self.assertTrue(codebase_merger.should_include_file(
            os.path.join(self.test_dir.name, "src", "main", "app.py")
        ))
        
        # Test binary file
        self.assertFalse(codebase_merger.should_include_file(
            os.path.join(self.test_dir.name, "binary_file.bin")
        ))
    
    @patch('codebase_merger.clone_repo')
    def test_process_repository(self, mock_clone):
        # Skip the clone step
        mock_clone.return_value = True
        
        # Process the test repository
        output_file = os.path.join(self.test_dir.name, "output.txt")
        file_count = codebase_merger.process_repository(self.test_dir.name, output_file)
        
        # Check results
        self.assertEqual(file_count, 3)  # Should process 3 files (README.md, app.py, test_app.py)
        
        # Verify the output file exists and contains headers for each file
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, "r") as f:
            content = f.read()
            self.assertIn("FILE: README.md", content)
            self.assertIn("FILE: src/main/app.py", content)
            self.assertIn("FILE: src/test/test_app.py", content)
            self.assertNotIn("FILE: binary_file.bin", content)  # Binary file should be excluded
            self.assertNotIn("FILE: .git/", content)  # .git directory should be ignored

if __name__ == "__main__":
    unittest.main() 