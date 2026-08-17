import unittest
from pathlib import Path


TEST_DIRECTORY = Path(__file__).parent / "tests"


def run_all_tests():
    test_suite = unittest.defaultTestLoader.discover(
        str(TEST_DIRECTORY),
        pattern="test_*.py",
    )

    test_runner = unittest.TextTestRunner(
        verbosity=2
    )
    test_result = test_runner.run(test_suite)

    return test_result.wasSuccessful()

if __name__ == "__main__":
    tests_passed = run_all_tests()

    if tests_passed:
        print()
        print("All automated tests passed.")
    else:
        print()
        print("One or more automated tests failed.")
        raise SystemExit(1)