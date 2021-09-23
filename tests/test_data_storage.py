import pytest
import json

from src.dataset import DataSet, DataSetException, DataLoadException

USER_DATASET = DataSet("Users", json_path="data/users.json")


def test_dataset_creation_with_no_data():
    with pytest.raises(DataLoadException):
        d = DataSet("testset")


def test_dataset_creation_with_json():
    with open("data/users.json", "r") as json_f:
        assert len(USER_DATASET) == len(json.load(json_f))


def test_dataset_creation_with_parsed_data():
    parsed_data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
    new_dataset = DataSet("X", _parsed_data=parsed_data)

    assert len(new_dataset) == len(parsed_data)


def test_dataset_creation_with_json_and_parsed_data():
    with pytest.raises(DataLoadException):
        _ = DataSet("X", json_path="data/users.json", _parsed_data=USER_DATASET._data)


def test_dataset_creation_with_non_list_json():
    with pytest.raises(DataLoadException):
        _ = DataSet("X", json_path="tests/data/non_list.json")


def test_dataset_creation_with_non_list_parsed_data():
    with pytest.raises(DataLoadException):
        _ = DataSet("X", _parsed_data={"some_field": "some_data"})


def test_dataset_creation_with_mixed_type_field():
    test_data = [{"name": "Larry", "age": 26}, {"name": "David", "age": "24"}]
    with pytest.raises(DataLoadException):
        _ = DataSet("X", _parsed_data=test_data)


def test_dataset_creation_with_mixed_type_list_field():
    test_data = [{"name": "Larry", "favourite_numbers": [1, "2"]}]
    with pytest.raises(DataLoadException):
        _ = DataSet("X", _parsed_data=test_data)

def test_dataset_creation_with_null_field():
    test_data = [{"name": "Larry", "credit_card_number": None}]
    with pytest.raises(DataLoadException):
        _ = DataSet("X", _parsed_data=test_data)


def test_dataset_creation_with_illegal_field_name():
    test_data = [{"name": "Larry", "_foreign_fields": 1}]

    # from a parsed dataset this is allowed, as joined fields
    # are passed down to children, so this may exist already
    data_set = DataSet("X", _parsed_data=test_data)
    assert len(data_set) == 1

    with pytest.raises(DataLoadException):
        _ = DataSet("X", json_path="tests/data/illegal_field.json")


def test_string_filtering():
    test_data = [
        {"name": "Larry"},
        {"name": "David"},
        {"name": "Rachel"},
    ]

    dataset = DataSet("People", _parsed_data=test_data)
    filtered_dataset = dataset.filter_by_value("name", "Larry")

    assert len(filtered_dataset) == 1
    assert filtered_dataset.data[0]["name"] == "Larry"


def test_int_filtering():
    test_data = [
        {"name": "Larry", "age": 26},
        {"name": "David", "age": 26},
        {"name": "Rachel", "age": 44},
    ]

    dataset = DataSet("People", _parsed_data=test_data)
    filtered_dataset = dataset.filter_by_value("age", 26)

    assert len(filtered_dataset) == 2
    assert {row["name"] for row in filtered_dataset.data} == {"Larry", "David"}


def test_float_filtering():
    test_data = [
        {"name": "Larry", "age": 26.41},
        {"name": "David", "age": 26.4},
        {"name": "Rachel", "age": 44.0},
    ]

    dataset = DataSet("People", _parsed_data=test_data)
    filtered_dataset = dataset.filter_by_value("age", 26.4)

    assert len(filtered_dataset) == 1
    assert filtered_dataset.data[0]["name"] == "David"


def test_bool_filtering():
    test_data = [
        {"name": "Larry", "age": 26, "verified": False},
        {"name": "David", "age": 26, "verified": True},
        {"name": "Rachel", "age": 44, "verified": True},
    ]

    dataset = DataSet("People", _parsed_data=test_data)
    filtered_dataset = dataset.filter_by_value("verified", False)

    assert len(filtered_dataset) == 1
    assert filtered_dataset.data[0]["name"] == "Larry"


def test_list_filtering():
    test_data = [
        {"name": "Larry", "age": 26, "skills": ["python", "sql"]},
        {"name": "David", "age": 26, "skills": ["java", "excel"]},
        {"name": "Rachel", "age": 44, "skills": ["java", "sql"]},
    ]

    dataset = DataSet("People", _parsed_data=test_data)
    filtered_dataset = dataset.filter_by_value("skills", "python")

    assert len(filtered_dataset) == 1
    assert filtered_dataset.data[0]["name"] == "Larry"

    filtered_dataset = dataset.filter_by_value("skills", "sql")
    assert len(filtered_dataset) == 2
    assert {row["name"] for row in filtered_dataset.data} == {"Larry", "Rachel"}


def test_filtering_with_invalid_type():
    test_data = [
        {"name": "Larry"},
        {"name": "David"},
        {"name": "Rachel"},
    ]

    dataset = DataSet("People", _parsed_data=test_data)

    with pytest.raises(DataSetException):
        _ = dataset.filter_by_value("name", 23)


def test_relating_dataset():
    user_data = [
        {"name": "Larry", "position_id": 1},
        {"name": "David", "position_id": 2},
        {"name": "Rachel", "position_id": 2},
        {"name": "Heather"},
    ]

    position_data = [{"id": 1, "title": "Programmer"}, {"id": 2, "title": "Engineer"}]

    user_dataset = DataSet("Users", _parsed_data=user_data)
    position_dataset = DataSet("Positions", _parsed_data=position_data)
    user_dataset.relate_dataset(position_dataset, "position_id", "id")

    larrys_positions = user_dataset.filter_by_value("name", "Larry").data[0][
        "_foreign_fields"
    ]["Positions"]

    assert len(larrys_positions) == 1
    assert larrys_positions[0]["title"] == "Programmer"

    # Heather didn't have a position_id, and therefore should not have any foreign fields
    assert (
        "_foreign_fields"
        not in user_dataset.filter_by_value("name", "Heather").data[0].keys()
    )


def test_relating_dataset_with_existing_name():
    user_data = [
        {"name": "Larry", "position_id": 1},
        {"name": "David", "position_id": 2},
        {"name": "Rachel", "position_id": 2},
        {"name": "Heather"},
    ]

    position_data = [{"id": 1, "title": "Programmer"}, {"id": 2, "title": "Engineer"}]

    user_dataset = DataSet("Users", _parsed_data=user_data)
    position_dataset = DataSet("Positions", _parsed_data=position_data)
    duplicate_position_dataset = DataSet("Positions", _parsed_data=position_data)

    user_dataset.relate_dataset(position_dataset, "position_id", "id")

    with pytest.raises(DataSetException):
        user_dataset.relate_dataset(duplicate_position_dataset, "position_id", "id")
