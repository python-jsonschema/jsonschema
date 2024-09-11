from pathlib import Path
from tempfile import TemporaryDirectory
import os

import nox

ROOT = Path(__file__).parent
PACKAGE = ROOT / "jsonschema"
BENCHMARKS = PACKAGE / "benchmarks"
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.rst"
DOCS = ROOT / "docs"

INSTALLABLE = [
    nox.param(value, id=name) for name, value in [
        ("no-extras", str(ROOT)),
        ("format", f"{ROOT}[format]"),
        ("format-nongpl", f"{ROOT}[format-nongpl]"),
    ]
]
REQUIREMENTS = dict(
    docs=DOCS / "requirements.txt",
)
REQUIREMENTS_IN = [  # this is actually ordered, as files depend on each other
    path.parent / f"{path.stem}.in" for path in REQUIREMENTS.values()
]

NONGPL_LICENSES = [
    "Apache Software License",
    "BSD License",
    "ISC License (ISCL)",
    "MIT License",
    "Mozilla Public License 2.0 (MPL 2.0)",
    "Python Software Foundation License",
    "The Unlicense (Unlicense)",
]

SUPPORTED = ["3.9", "3.10", "pypy3.10", "3.11", "3.12", "3.13"]
LATEST_STABLE = "3.12"

nox.options.sessions = []


def session(default=True, python=LATEST_STABLE, **kwargs):  # noqa: D103
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(python=python, **kwargs)(fn)

    return _session


@session(python=SUPPORTED)
@nox.parametrize("installable", INSTALLABLE)
def tests(session, installable):
    """
    Run the test suite with a corresponding Python version.
    """
    env = dict(JSON_SCHEMA_TEST_SUITE=str(ROOT / "json"))

    session.install("virtue", installable)

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            posargs = session.posargs[2:]
            github = Path(os.environ["GITHUB_STEP_SUMMARY"])
        else:
            posargs, github = session.posargs[1:], None

        session.install("coverage[toml]")
        session.run(
            "coverage",
            "run",
            *posargs,
            "-m",
            "virtue",
            PACKAGE,
            env=env,
        )

        if github is None:
            session.run("coverage", "report")
        else:
            with github.open("a") as summary:
                summary.write("### Coverage\n\n")
                summary.flush()  # without a flush, output seems out of order.
                session.run(
                    "coverage",
                    "report",
                    "--format=markdown",
                    stdout=summary,
                )
    else:
        session.run("virtue", *session.posargs, PACKAGE, env=env)


@session()
@nox.parametrize("installable", INSTALLABLE)
def audit(session, installable):
    """
    Audit dependencies for vulnerabilities.
    """
    session.install("pip-audit", installable)
    session.run("python", "-m", "pip_audit")


@session()
def license_check(session):
    """
    Check that the non-GPL extra does not allow arbitrary licenses.
    """
    session.install("pip-licenses", f"{ROOT}[format-nongpl]")
    session.run(
        "python",
        "-m",
        "piplicenses",
        "--ignore-packages",
        "pip-requirements-parser",
        "pip_audit",
        "pip-api",
        "--allow-only",
        ";".join(NONGPL_LICENSES),
    )


@session(tags=["build"])
def build(session):
    """
    Build a distribution suitable for PyPI and check its validity.
    """
    session.install("build", "docutils", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")
        session.run(
            "python", "-m", "docutils", "--strict", CHANGELOG, os.devnull,
        )


@session()
def secrets(session):
    """
    Check for accidentally committed secrets.
    """
    session.install("detect-secrets")
    session.run("detect-secrets", "scan", ROOT)


@session(tags=["style"])
def style(session):
    """
    Check Python code style.
    """
    session.install("ruff")
    session.run("ruff", "check", ROOT)


@session()
def typing(session):
    """
    Check static typing.
    """
    session.install("mypy", "types-requests", ROOT)
    session.run("mypy", "--config", PYPROJECT, PACKAGE)


@session(tags=["docs"])
@nox.parametrize(
    "builder",
    [
        nox.param(name, id=name)
        for name in [
            "dirhtml",
            "doctest",
            "linkcheck",
            "man",
            "spelling",
        ]
    ],
)
def docs(session, builder):
    """
    Build the documentation using a specific Sphinx builder.
    """
    session.install("-r", REQUIREMENTS["docs"])
    with TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        argv = ["-n", "-T", "-W"]
        if builder != "spelling":
            argv += ["-q"]
        posargs = session.posargs or [tmpdir / builder]
        session.run(
            "python",
            "-m",
            "sphinx",
            "-b",
            builder,
            DOCS,
            *argv,
            *posargs,
        )


@session(tags=["docs", "style"], name="docs(style)")
def docs_style(session):
    """
    Check the documentation style.
    """
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", "--config", PYPROJECT, DOCS)


@session(default=False)
@nox.parametrize(
    "benchmark",
    [
        nox.param(each.stem, id=each.stem)
        for each in BENCHMARKS.glob("[!_]*.py")
    ],
)
def bench(session, benchmark):
    """
    Run a performance benchmark.
    """
    session.install("pyperf", f"{ROOT}[format]")
    tmpdir = Path(session.create_tmp())
    output = tmpdir / f"bench-{benchmark}.json"
    session.run("python", BENCHMARKS / f"{benchmark}.py", "--output", output)


@session(default=False)
def requirements(session):
    """
    Update the project's pinned requirements.

    You should commit the result afterwards.
    """
    session.install("pip-tools")
    for each in REQUIREMENTS_IN:
        session.run(
            "pip-compile",
            "--resolver",
            "backtracking",
            "--strip-extras",
            "-U",
            each.relative_to(ROOT),
        )
