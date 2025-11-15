"""
Executable entry point for the `bench` package.

I keep this file intentionally minimal: all real logic lives in
`bench.cli.main()`, and this module simply delegates to it.

This allows:

    python -m bench ...

to behave exactly like a proper command-line tool, even without
declaring an installed console script entry point.
"""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    # For v1 I run the CLI directly.
    # If I publish this as an installable package later, I can also
    # expose "bench" as a console script in pyproject.toml.
    main()
