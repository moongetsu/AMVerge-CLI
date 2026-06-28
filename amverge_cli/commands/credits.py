from __future__ import annotations

from rich.panel import Panel

from ..ui import banner, console, make_table


def credits() -> None:
    """Show the AMVerge contributors."""
    banner("credits")

    team = [
        ("Crptk",          "App owner · developer · original creator"),
        ("Netsuma",         "Export settings · UI upgrades"),
        ("Moongetsu",       "Settings overhaul · Discord RPC · menu revamp · CLI"),
        ("Lewis",           "Mac support · background import · heavy optimization"),
        ("0xkhaosoccured",  "Grid UI fixes"),
        ("TOSINIRL",        "Mac video import fixes"),
    ]

    console.print("  [bright_black]The people who made AMVerge come to life.[/]\n")

    t = make_table(
        ("name",  "#22c55e bold", {"width": 18}),
        ("role",  "bright_black", {}),
        title="Contributors",
    )
    for name, role in team:
        t.add_row(name, role)
    console.print(t)

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
