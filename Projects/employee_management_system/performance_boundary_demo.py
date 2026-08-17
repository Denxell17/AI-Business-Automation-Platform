from payroll import determine_performance


def run_performance_boundary_test():
    test_scores = [
        -1,
        0,
        69,
        70,
        79,
        80,
        89,
        90,
        100,
        101,
    ]

    print("=" * 45)
    print("PERFORMANCE BOUNDARY TEST".center(45))
    print("=" * 45)

    for score in test_scores:
        rating, bonus_rate = determine_performance(score)

        print(
            f"Score: {score:>3} | "
            f"Rating: {rating:<18} | "
            f"Bonus: {bonus_rate:.0%}"
        )


if __name__ == "__main__":
    run_performance_boundary_test()