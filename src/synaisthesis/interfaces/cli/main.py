from typing import Annotated

import typer

from synaisthesis.interfaces.cli.commands.project import app as project_app
from synaisthesis.version import get_version

app = typer.Typer(no_args_is_help=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(get_version())
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the Synaisthesis version and exit.",
        ),
    ] = False,
) -> None:
    pass


app.add_typer(project_app, name="project")
