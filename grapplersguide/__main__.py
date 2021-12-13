import typer

app = typer.Typer()


@app.command()
def download(name: str):
    typer.echo(f"Hello {name}")


if __name__ == "__main__":
    app()
