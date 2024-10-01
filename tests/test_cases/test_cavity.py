import os
import stat
import sys
from pathlib import Path
from typing import Sequence

if sys.version_info >= (3, 9):
    from collections.abc import Generator
else:
    from typing import Generator

import pytest
from foamlib import FoamCase


@pytest.fixture(params=[False, True])
def cavity(request: pytest.FixtureRequest) -> "Generator[FoamCase]":
    tutorials_path = Path(os.environ["FOAM_TUTORIALS"])
    path = tutorials_path / "incompressible" / "icoFoam" / "cavity" / "cavity"
    of11_path = tutorials_path / "incompressibleFluid" / "cavity"

    case = FoamCase(path if path.exists() else of11_path)

    with case.clone() as clone:
        if request.param:
            run = clone.path / "run"
            assert not run.exists()
            assert not (clone.path / "Allrun").exists()
            run.write_text(
                "#!/usr/bin/env python3\nfrom pathlib import Path\nfrom foamlib import FoamCase\nFoamCase(Path(__file__).parent).run(parallel=False)"
            )
            run.chmod(run.stat().st_mode | stat.S_IEXEC)

            clean = clone.path / "clean"
            assert not clean.exists()
            assert not (clone.path / "Allclean").exists()
            clean.write_text(
                "#!/usr/bin/env python3\nfrom pathlib import Path\nfrom foamlib import FoamCase\nFoamCase(Path(__file__).parent).clean()"
            )
            clean.chmod(clean.stat().st_mode | stat.S_IEXEC)

        yield clone


def test_run(cavity: FoamCase) -> None:
    cavity.run(parallel=False)
    cavity.clean()
    cavity.run(parallel=False)
    assert len(cavity) > 0
    internal = cavity[-1]["U"].internal_field
    assert isinstance(internal, Sequence)
    assert len(internal) == 400


def test_double_clean(cavity: FoamCase) -> None:
    cavity.clean()
    cavity.clean(check=True)
    cavity.run(parallel=False)