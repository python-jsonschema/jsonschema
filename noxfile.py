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

NONGPL_LICENSES = [
    "Apache Software License",
    "BSD License",
    "ISC License (ISCL)",
    "MIT License",
    "Mozilla Public License 2.0 (MPL 2.0)",
    "Python Software Foundation License",
    "The Unlicense (Unlicense)",
]


nox.options.sessions = []


def session(default=True, **kwargs):
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(**kwargs)(fn)

    return _session


@session(python=["3.8", "3.9", "3.10", "3.11", "pypy3"])
@nox.parametrize("installable", INSTALLABLE)
def tests(session, installable):

    env = dict(JSON_SCHEMA_TEST_SUITE=str(ROOT / "json"))

    session.install("virtue", installable)

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            posargs = session.posargs[2:]
            github = os.environ["GITHUB_STEP_SUMMARY"]
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
            with open(github, "a") as summary:
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
    session.install("pip-audit", installable)
    session.run("python", "-m", "pip_audit")

    if "format-nongpl" in installable:
        session.install("pip-licenses")
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
    session.install("build", "docutils", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")
        session.run(
            "python", "-m", "docutils", "--strict", CHANGELOG, os.devnull,
        )


@session()
def secrets(session):
    session.install("detect-secrets")
    session.run("detect-secrets", "scan", ROOT)


@session(tags=["style"])
def style(session):
    session.install("ruff")
    session.run("ruff", "check", ROOT)


@session()
def typing(session):
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
    session.install("-r", DOCS / "requirements.txt")
    with TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        argv = ["-n", "-T", "-W"]
        if builder != "spelling":
            argv += ["-q"]
        session.run(
            "python",
            "-m",
            "sphinx",
            "-b",
            builder,
            DOCS,
            tmpdir / builder,
            *argv,
        )


@session(tags=["docs", "style"], name="docs(style)")
def docs_style(session):
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", "--config", PYPROJECT, DOCS)


@session(default=False)
def bandit(session):
    session.install("bandit")
    session.run("bandit", "--recursive", PACKAGE)


@session(default=False)
@nox.parametrize(
    "benchmark",
    [
        nox.param(each.stem, id=each.stem)
        for each in BENCHMARKS.glob("[!_]*.py")
    ],
)
def perf(session, benchmark):
    session.install("pyperf", f"{ROOT}[format]")
    tmpdir = Path(session.create_tmp())
    output = tmpdir / f"bench-{benchmark}.json"
    session.run("python", BENCHMARKS / f"{benchmark}.py", "--output", output)


@session(default=False)
def requirements(session):
    session.install("pip-tools")
    for each in [DOCS / "requirements.in", ROOT / "test-requirements.in"]:
        session.run(
            "pip-compile",
            "--resolver",
            "backtracking",
            "-U",
            each.relative_to(ROOT),
        )
