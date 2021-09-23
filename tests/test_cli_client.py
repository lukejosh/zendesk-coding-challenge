import pytest
from src.cli_client import CLIClient, CLIException
from src.dataset import DataSet


def _click_prompt_mock(_text, type):
    """Mocks click.prompt

    When prompted for a data type, it will return a static value.
    When prompted for a choice of values, it will return the first value

    Args:
        type:
            type of return value, or a Click.choice parameter
            (horrible variable name copied from the click function declaration)
    """
    if type == int:
        return 1
    elif type == float:
        return 1.0
    elif type == str:
        return "a"
    elif type == bool:
        return True
    else:
        return type.choices[0]


def _click_echo_mock(text):
    return text


def test_format_question_with_no_type_or_options(mocker):
    mocker.patch("click.prompt", _click_prompt_mock)
    client = CLIClient([])

    with pytest.raises(CLIException):
        client.format_question("How are you today?")


def test_format_question_with_type_and_response(mocker):
    mocker.patch("click.prompt", _click_prompt_mock)
    client = CLIClient([])

    with pytest.raises(CLIException):
        client.format_question(
            "How are you today?", response_type=str, options=["Good", "Bad"]
        )


def test_format_question_with_response_type(mocker):
    mocker.patch("click.prompt", _click_prompt_mock)
    client = CLIClient([])
    assert client.format_question("How are you today?", response_type=str) == "a"


def test_format_question_with_response_options(mocker):
    mocker.patch("click.prompt", _click_prompt_mock)
    client = CLIClient([])
    assert (
        client.format_question("How are you today?", options=["Good", "Bad"]) == "Good"
    )


def test_formatting_of_empty_dataset(mocker):
    mocker.patch("click.echo", _click_echo_mock)
    client = CLIClient([])
    data_set = DataSet("X", _parsed_data=[])

    assert client.format_data(data_set) == "No results returned"


def test_formatting_of_dataset_with_no_join(mocker):
    mocker.patch("click.echo", _click_echo_mock)
    client = CLIClient([])

    data_set = [{"name": "Henry"}, {"name": "Elly"}]
    data_set = DataSet("X", _parsed_data=data_set)

    assert client.format_data(data_set) == f"name\tHenry\n\nname\tElly"


def test_formatting_of_dataset_with_join(mocker):
    mocker.patch("click.echo", _click_echo_mock)
    client = CLIClient([])

    people_data = [
        {"name": "Henry", "location_id": 1},
        {"name": "Elly", "location_id": 2},
    ]
    location_data = [{"id": 1, "name": "Victoria"}, {"id": 2, "name": "Queensland"}]

    people_data_set = DataSet(name="People", _parsed_data=people_data)
    location_data_set = DataSet(name="Locations", _parsed_data=location_data)

    people_data_set.relate_dataset(location_data_set, "location_id", "id")

    expected_string = (
        "location_id\t1\n"
        "name\tHenry\n"
        "Locations\n"
        "\t__________\n"
        "\tid\t1\n"
        "\tname\tVictoria\n\n"
        "location_id\t2\n"
        "name\tElly\n"
        "Locations\n"
        "\t__________\n"
        "\tid\t2\n"
        "\tname\tQueensland"

    )

    assert client.format_data(people_data_set) == expected_string
