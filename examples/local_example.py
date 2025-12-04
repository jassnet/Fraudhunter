"""
Compatibility shim for running the bundled local example outside editable installs.
Prefer: `python -m fraud_checker.examples.local_example`
"""

from fraud_checker.examples.local_example import main


if __name__ == "__main__":
    main()
