import pytest

from agentgrade.checks import answer_has_number, numbers_in


def test_numbers_in_extracts_decimals_signs_and_thousands():
    assert numbers_in("cost $12.50, was -3 and 1,250.5 total") == [12.5, -3.0, 1250.5]


@pytest.mark.parametrize(
    "answer, passed",
    [
        ("The shipping cost is $12.50.", True),
        ("12.5 USD", True),
        ("It costs 112.5 USD", False),  # substring check would wrongly pass this
        ("It costs 12.55 USD", False),
        ("I could not find it", False),
        ("", False),
        (None, False),
    ],
)
def test_answer_has_number(answer, passed):
    assert answer_has_number(answer, 12.5) is passed
