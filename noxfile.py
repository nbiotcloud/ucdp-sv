#
# MIT License
#
# Copyright (c) 2024 nbiotcloud
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
NOX Configuration.

See [NOX Documentation](https://nox.thea.codes/en/stable/) for further details
"""

import os
import pathlib
import shutil

import nox

os.environ.update(
    {
        "PDM_IGNORE_SAVED_PYTHON": "1",
        "LANGUAGE": "en_US",
    }
)
nox.options.sessions = ["format", "test", "testsv", "checkdeps", "checktypes", "doc"]


@nox.session()
def format(session: nox.Session) -> None:
    """Run Code Formatter and Checks."""
    _init(session)
    session.run_always("pdm", "install", "-G", "format")
    session.run("pre-commit", "run", "--all-files")


@nox.session()
def test(session: nox.Session) -> None:
    """Run Test - Additional Arguments are forwarded to `pytest`."""
    _init(session)
    session.run_always("pdm", "install", "-G", "test")
    session.run("pytest", "-vv", *session.posargs)
    htmlcovfile = pathlib.Path().resolve() / "htmlcov" / "index.html"
    print(f"Coverage report:\n\n    file://{htmlcovfile!s}\n")


@nox.session()
def checkdeps(session: nox.Session) -> None:
    """Check Dependencies."""
    _init(session)
    session.run_always("pdm", "install")
    session.run("python", "-c", "import ucdpsv")


@nox.session()
def checktypes(session: nox.Session) -> None:
    """Run Type Checks."""
    _init(session)
    session.run_always("pdm", "install", "-G", "checktypes")
    session.run("mypy", "src", "tests")


@nox.session()
def doc(session: nox.Session) -> None:
    """Build Documentation."""
    _init(session)
    session.run_always("pdm", "install", "-G", "doc")
    session.run("mkdocs", "build")
    shutil.make_archive("docs", "zip", "site")
    docindexfile = pathlib.Path().resolve() / "site" / "index.html"
    print(f"Documentation is available at:\n\n    file://{docindexfile!s}\n")


@nox.session(name="doc-serve")
def doc_serve(session: nox.Session) -> None:
    """Build Documentation and serve via HTTP."""
    _init(session)
    session.run_always("pdm", "install", "-G", "doc")
    session.run("mkdocs", "serve", "--no-strict")


@nox.session()
def dev(session: nox.Session) -> None:
    """Development Environment - Additional Arguments Are Executed."""
    _init(session)
    session.run_always("pdm", "install", "-G", ":all")
    session.run("pip", "install", "-e", ".")
    if session.posargs:
        session.run(*session.posargs, external=True)


@nox.session()
def testsv(session: nox.Session) -> None:
    """Run System Verilog Tests - Additional Arguments are forwarded to `pytest`."""
    _init(session)
    session.run_always("pdm", "install", "-G", ":all")
    with session.chdir("tests"):
        session.run("pytest", "-vvsrA", "regression.py", *session.posargs)


def _init(session: nox.Session):
    session.install("pdm")
    lockfile = pathlib.Path("pdm.lock")

    if not lockfile.exists():
        session.run("pdm", "lock")
