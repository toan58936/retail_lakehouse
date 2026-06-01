#!/usr/bin/env python
# CLI.py - Command Line Interface for Retail Lakehouse
import typer

from pipeline.config import settings


app = typer.Typer(
    name="retail-lakehouse",
    help="Retail Sales Modern Data Lakehouse CLI",
    add_completion=True,
)


@app.command()
def init():
    """Initialize project directories."""
    settings.ensure_directories()
    typer.echo("Project initialized successfully!")
    typer.echo(f"ENV: {settings.ENV} | Storage: {settings.STORAGE_ROOT}")


@app.command()
def bronze(
    mode: str = typer.Option(
        "sample",
        "--mode",
        "--env",
        help="Bronze run mode: sample, full/production, or all.",
    )
):
    """Run Bronze Layer ingestion."""
    from pipeline.bronze.ingestor import ingest_all_raw_data, normalize_env_mode

    try:
        normalized_mode = normalize_env_mode(mode)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Running Bronze ingestion [{normalized_mode}]")
    summary = ingest_all_raw_data(env_mode=normalized_mode)

    total_files = summary["total_files"]
    success_count = summary["success_count"]
    if total_files == 0:
        typer.secho("No CSV files found for this Bronze mode.", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    if success_count != total_files:
        typer.secho(
            f"Bronze ingestion failed: {success_count}/{total_files} files succeeded. "
            "Check logs/pipeline.log for details.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    typer.echo(f"Bronze ingestion completed: {success_count}/{total_files} files succeeded.")


@app.command()
def status():
    """Show current configuration."""
    typer.echo("Current Configuration:")
    typer.echo(f"   ENV            : {settings.ENV}")
    typer.echo(f"   STORAGE_ROOT   : {settings.STORAGE_ROOT}")
    typer.echo(f"   BATCH_SIZE     : {settings.BATCH_SIZE}")
    typer.echo(f"   LOG_FILE       : {settings.LOG_FILE}")


if __name__ == "__main__":
    app()
