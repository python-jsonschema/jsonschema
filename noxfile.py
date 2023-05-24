from pathlib import Path

import nox

ROOT = Path(__file__).parent
PACKAGE = ROOT / "jsonschema"
BENCHMARKS = PACKAGE / "benchmarks"
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.rst"
DOCS = ROOT / "docs"

INSTALLABLE = [
    nox.param(value, id=name) for name, value in [
        ("no-extras", ROOT),
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

    if session.posargs and session.posargs[0] in {"coverage", "ghcoverage"}:
        ghcoverage = session.posargs.pop(0) == "ghcoverage"

        session.install("coverage[toml]")
        session.run(
            "coverage",
            "run",
            *session.posargs,
            "-m",
            "virtue",
            PACKAGE,
            env=env,
        )
        session.run("coverage", "report")

        if ghcoverage:
            session.run(
                "sh",
                ROOT / ".github/coverage.sh",
                f"{session.bin}/python",
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
    session.install("build")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)


@session(tags=["style"])
def readme(session):
    session.install("build", "docutils", "twine")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
    session.run("python", "-m", "twine", "check", tmpdir + "/*")
    session.run("rst2html5.py", "--halt=warning", CHANGELOG, "/dev/null")


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
    tmpdir = Path(session.create_tmp())
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
