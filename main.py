from importlib.metadata import version


def main() -> None:
    import mellea  # noqa: F401  (verifies the install)

    print(f"mellea-resume-readiness is set up. Mellea version: {version('mellea')}")


if __name__ == "__main__":
    main()
