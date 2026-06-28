import typer

from .commands.detect import detect
from .commands.export import export
from .commands.merge import merge
from .commands.info import info

app = typer.Typer(
    name="amverge",
    help="AMVerge CLI — scene detection and clip management.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.command()(detect)
app.command()(export)
app.command()(merge)
app.command()(info)


if __name__ == "__main__":
    app()
