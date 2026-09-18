"""Configuration and package contracts introduced by the structure refactor."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from app.core.config import BACKEND_DIR, PROJECT_ROOT, DATA_DIR, ENV_FILE, database_url

class ConfigurationTests(unittest.TestCase):
    def test_repository_paths(self):
        self.assertEqual(DATA_DIR, PROJECT_ROOT/'data')
        self.assertEqual(ENV_FILE, BACKEND_DIR/'.env')
        self.assertTrue((PROJECT_ROOT/'database/schema.sql').is_file())

    def test_missing_configuration_fails_explicitly(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError,'DATABASE_URL'):
            database_url()

    def test_explicit_environment_precedence(self):
        with patch.dict(os.environ, {'DATABASE_URL':'sqlite:///:memory:'}):
            self.assertEqual(database_url(),'sqlite:///:memory:')

if __name__=='__main__':unittest.main()
