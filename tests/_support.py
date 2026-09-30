"""Shared test paths and imports for the non-packaged runtime tooling."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
SCRIPTS = ROOT / "app" / "Scripts"
FIXTURES = TESTS / "fixtures"
GAMES_BLUEPRINT = ROOT / "app" / "Blueprints" / "Games"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
