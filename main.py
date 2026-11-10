"""Entry point for the Resume Skills-Gap Analyzer.

For now this is a smoke check confirming the environment is set up and
Mellea is importable. Replace with the real app as features land.
"""

from importlib.metadata import version


def main() -> None:
    import mellea  # noqa: F401  (verifies the install)

    print(f"mellea-resume-readiness is set up. Mellea version: {version('mellea')}")


if __name__ == "__main__":
    main()
