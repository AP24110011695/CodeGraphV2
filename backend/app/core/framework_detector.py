"""Framework detection from repository manifest files.

Scans well-known manifest files in the repository source tree and returns
a list of detected framework/library names.  Detection is purely textual
(JSON parsing or substring matching) — no execution of manifest tooling.
"""

from __future__ import annotations

import json
import re
from contextlib import suppress
from pathlib import Path

# ---------------------------------------------------------------------------
# Known framework / library patterns
# ---------------------------------------------------------------------------

# npm / package.json: map dependency package name → framework label
_NPM_FRAMEWORKS: dict[str, str] = {
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "nuxt": "Nuxt.js",
    "vue": "Vue",
    "@vue/core": "Vue",
    "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit",
    "angular": "Angular",
    "@angular/core": "Angular",
    "express": "Express",
    "fastify": "Fastify",
    "koa": "Koa",
    "hapi": "@hapi/hapi",
    "nestjs": "NestJS",
    "@nestjs/core": "NestJS",
    "remix": "Remix",
    "@remix-run/react": "Remix",
    "gatsby": "Gatsby",
    "astro": "Astro",
    "solid-js": "SolidJS",
    "electron": "Electron",
    "jest": "Jest",
    "vitest": "Vitest",
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",
    "tailwindcss": "Tailwind CSS",
    "prisma": "Prisma",
    "typeorm": "TypeORM",
    "mongoose": "Mongoose",
    "graphql": "GraphQL",
    "apollo-server": "Apollo",
    "@apollo/server": "Apollo",
    "socket.io": "Socket.IO",
    "rxjs": "RxJS",
    "redux": "Redux",
    "zustand": "Zustand",
    "mobx": "MobX",
    "axios": "Axios",
}

# Python requirements.txt / pyproject.toml: package name → framework label
_PYTHON_FRAMEWORKS: dict[str, str] = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "aiohttp": "aiohttp",
    "sanic": "Sanic",
    "falcon": "Falcon",
    "bottle": "Bottle",
    "pyramid": "Pyramid",
    "litestar": "Litestar",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
    "pydantic": "Pydantic",
    "celery": "Celery",
    "pytest": "pytest",
    "numpy": "NumPy",
    "pandas": "pandas",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "transformers": "HuggingFace Transformers",
    "langchain": "LangChain",
    "openai": "OpenAI SDK",
    "anthropic": "Anthropic SDK",
    "requests": "Requests",
    "httpx": "HTTPX",
    "redis": "Redis",
    "motor": "Motor",
    "beanie": "Beanie",
    "tortoise-orm": "Tortoise ORM",
    "graphene": "Graphene",
    "strawberry-graphql": "Strawberry",
}

# Rust Cargo.toml
_RUST_FRAMEWORKS: dict[str, str] = {
    "actix-web": "Actix Web",
    "axum": "Axum",
    "warp": "Warp",
    "rocket": "Rocket",
    "tokio": "Tokio",
    "serde": "Serde",
    "diesel": "Diesel",
    "sqlx": "SQLx",
    "reqwest": "Reqwest",
    "tonic": "Tonic (gRPC)",
    "tauri": "Tauri",
}

# Go go.mod
_GO_FRAMEWORKS: dict[str, str] = {
    "gin-gonic/gin": "Gin",
    "labstack/echo": "Echo",
    "gofiber/fiber": "Fiber",
    "gorilla/mux": "Gorilla Mux",
    "go-chi/chi": "Chi",
    "julienschmidt/httprouter": "httprouter",
    "beego/beego": "Beego",
    "go-gorm/gorm": "GORM",
    "jinzhu/gorm": "GORM",
    "spf13/cobra": "Cobra",
    "urfave/cli": "urfave/cli",
    "grpc/grpc-go": "gRPC",
}

# Java pom.xml / build.gradle (substring matches in file text)
_JAVA_FRAMEWORKS: list[tuple[str, str]] = [
    ("spring-boot", "Spring Boot"),
    ("spring-framework", "Spring Framework"),
    ("springframework", "Spring Framework"),
    ("quarkus", "Quarkus"),
    ("micronaut", "Micronaut"),
    ("jakarta.ee", "Jakarta EE"),
    ("javax.servlet", "Java EE"),
    ("hibernate", "Hibernate"),
    ("mybatis", "MyBatis"),
    ("junit", "JUnit"),
    ("mockito", "Mockito"),
    ("vertx", "Vert.x"),
    ("grpc", "gRPC"),
]


# ---------------------------------------------------------------------------
# Per-manifest parsers
# ---------------------------------------------------------------------------


def _detect_npm(source_root: Path) -> list[str]:
    """Detect frameworks from ``package.json``."""
    pkg_path = source_root / "package.json"
    if not pkg_path.is_file():
        return []
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return []

    all_deps: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        all_deps.update(data.get(section, {}).keys())

    found: list[str] = []
    seen: set[str] = set()
    for pkg, label in _NPM_FRAMEWORKS.items():
        if pkg in all_deps and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _detect_python_requirements(source_root: Path) -> list[str]:
    """Detect frameworks from ``requirements.txt``."""
    req_path = source_root / "requirements.txt"
    if not req_path.is_file():
        return []
    try:
        lines = req_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for line in lines:
        # Strip version specifiers and comments
        pkg = re.split(r"[>=<!;\s#\[]", line.strip())[0].lower()
        label = _PYTHON_FRAMEWORKS.get(pkg)
        if label and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _detect_python_pyproject(source_root: Path) -> list[str]:
    """Detect frameworks from ``pyproject.toml`` (simple text scan)."""
    pyproject_path = source_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return []
    try:
        text = pyproject_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for pkg, label in _PYTHON_FRAMEWORKS.items():
        if pkg in text and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _detect_rust_cargo(source_root: Path) -> list[str]:
    """Detect frameworks from ``Cargo.toml``."""
    cargo_path = source_root / "Cargo.toml"
    if not cargo_path.is_file():
        return []
    try:
        text = cargo_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for pkg, label in _RUST_FRAMEWORKS.items():
        if pkg in text and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _detect_go_mod(source_root: Path) -> list[str]:
    """Detect frameworks from ``go.mod``."""
    gomod_path = source_root / "go.mod"
    if not gomod_path.is_file():
        return []
    try:
        text = gomod_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for pkg, label in _GO_FRAMEWORKS.items():
        if pkg in text and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _detect_java(source_root: Path) -> list[str]:
    """Detect frameworks from ``pom.xml`` or ``build.gradle``."""
    text = ""
    for manifest in ("pom.xml", "build.gradle", "build.gradle.kts"):
        path = source_root / manifest
        if path.is_file():
            with suppress(OSError):
                text += path.read_text(encoding="utf-8", errors="replace").lower()


    if not text:
        return []

    found: list[str] = []
    seen: set[str] = set()
    for pattern, label in _JAVA_FRAMEWORKS:
        if pattern in text and label not in seen:
            found.append(label)
            seen.add(label)
    return found


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_frameworks(source_root: Path) -> list[str]:
    """Scan manifest files under *source_root* and return detected frameworks.

    Looks for the first-level subdirectory if *source_root* contains exactly
    one child directory (common for extracted zip archives).

    Args:
        source_root: Root of the extracted repository source tree.

    Returns:
        Sorted, deduplicated list of detected framework/library names.
    """
    # If the repo was extracted into a single top-level subdirectory, look
    # inside that as well (e.g. ``source/myrepo/package.json``).
    candidates: list[Path] = [source_root]
    children = [p for p in source_root.iterdir() if p.is_dir()]
    if len(children) == 1:
        candidates.append(children[0])

    all_frameworks: set[str] = set()
    for root in candidates:
        all_frameworks.update(_detect_npm(root))
        all_frameworks.update(_detect_python_requirements(root))
        all_frameworks.update(_detect_python_pyproject(root))
        all_frameworks.update(_detect_rust_cargo(root))
        all_frameworks.update(_detect_go_mod(root))
        all_frameworks.update(_detect_java(root))

    return sorted(all_frameworks)
