from __future__ import annotations

from rich.panel import Panel

from ..ui import banner, console, make_table


def credits() -> None:
    """Show the AMVerge contributors."""
    banner("credits")

    cli_team = [
        ("Moongetsu",  "CLI author · package design · interactive wizard"),
    ]

    app_team = [
        ("Crptk",          "App owner · developer · original creator"),
        ("Netsuma",         "Export settings · UI upgrades"),
        ("Moongetsu",       "Settings overhaul · Discord RPC · menu revamp"),
        ("Lewis",           "Mac support · background import · heavy optimization"),
        ("0xkhaosoccured",  "Grid UI fixes"),
        ("TOSINIRL",        "Mac video import fixes"),
    ]

    console.print("  [bright_black]The people behind AMVerge.[/]\n")

    t1 = make_table(
        ("name",  "#22c55e bold", {"width": 18}),
        ("role",  "bright_black", {}),
        title="AMVerge CLI",
    )
    for name, role in cli_team:
        t1.add_row(name, role)
    console.print(t1)

    t2 = make_table(
        ("name",  "#22c55e bold", {"width": 18}),
        ("role",  "bright_black", {}),
        title="AMVerge App",
    )
    for name, role in app_team:
        t2.add_row(name, role)
    console.print(t2)

    console.print()
    console.print(
        Panel(
            "[bright_black]Want to contribute?[/]  [white]github.com/crptk/AMVerge[/]",
            border_style="bright_black",
            padding=(0, 2),
            expand=False,
        )
    )
    console.print()
