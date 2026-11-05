"""Run each integration scenario in an isolated interpreter and temporary DB."""
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.parametrize("scenario", ["scenario_smoke.py", "scenario_extra.py", "scenario_simulator.py"])
def test_scenario(scenario):
    script = Path(__file__).parent / scenario
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=90, cwd=script.parents[1])
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
