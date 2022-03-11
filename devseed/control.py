import sys

import rich


def abort(msg):
    rich.print(f"[red]{msg}[/red]")
    sys.exit(1)
