"""Project CLI commands (blueprint 07, section 16: `synaisthesis project create`)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config

from synaisthesis.application.project_service import create_project, get_project
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonical_json
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.project_repository import project_state_dict

app = typer.Typer(no_args_is_help=True, help="Manage research projects.")

_MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "storage" / "migrations"

_DEFAULT_DATABASE_URL = "sqlite:///workspace/synaisthesis.db"
_DEFAULT_ARTIFACT_ROOT = "workspace/artifacts"

DatabaseUrl = Annotated[
    str,
    typer.Option(
        "--database-url",
        envvar="SYNAISTHESIS_DATABASE_URL",
        help="SQLAlchemy database URL.",
    ),
]
ArtifactRoot = Annotated[
    str,
    typer.Option(
        "--artifact-root",
        envvar="SYNAISTHESIS_ARTIFACT_ROOT",
        help="Directory for content-addressed artifacts.",
    ),
]


def _ensure_schema(database_url: str) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")


@app.command()
def create(
    name: Annotated[str, typer.Option("--name", "-n", help="Project name.")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Project description.")
    ] = "",
    database_url: DatabaseUrl = _DEFAULT_DATABASE_URL,
    artifact_root: ArtifactRoot = _DEFAULT_ARTIFACT_ROOT,
) -> None:
    """Create a project and persist its Project, Artifact and DomainEvent."""
    _ensure_schema(database_url)
    _, session_factory = init_database(database_url)
    with session_factory() as session:
        try:
            project = create_project(
                session,
                name=name,
                description=description,
                artifact_root=Path(artifact_root),
            )
            session.commit()
        except DomainError as exc:
            session.rollback()
            typer.echo(f"{exc.error_code}: {exc.message}", err=True)
            raise typer.Exit(1) from exc
    typer.echo(canonical_json(project_state_dict(project)))


@app.command()
def show(
    project_id: Annotated[str, typer.Option("--project-id", "-p", help="Project id to read.")],
    database_url: DatabaseUrl = _DEFAULT_DATABASE_URL,
    artifact_root: ArtifactRoot = _DEFAULT_ARTIFACT_ROOT,
) -> None:
    """Re-read a project from its persisted event stream."""
    _ensure_schema(database_url)
    _, session_factory = init_database(database_url)
    with session_factory() as session:
        try:
            project = get_project(session, project_id=project_id, artifact_root=Path(artifact_root))
        except DomainError as exc:
            typer.echo(f"{exc.error_code}: {exc.message}", err=True)
            raise typer.Exit(1) from exc
    typer.echo(canonical_json(project_state_dict(project)))
