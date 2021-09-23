# required so a class method's return type annotation can be the class itself
from __future__ import annotations

import json
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple


class DataLoadException(Exception):
    pass


class DataSetException(Exception):
    pass


DataSetRelation = namedtuple(
    "DataSetRelation", ["foreign_data_set", "field", "foreign_field"]
)


class DataSet:
    """A class used to parse, store, filter and join structured dataset(s).

    Allows for data to be loaded directly from a JSON file, or from a previously parsed
    dataset (intended for internal use only).

    The dataset is expected to be uniformly typed, i.e., each field across the dataset has the
    same type on each entry (with the exception of null). In the case of an array of values provided,
    it is expected that the type of values contained within the array is static (and does not contain
    nested arrays!)

    Attributes:
        name: Human readable name string
        fields: A list of fields in the data
        field_type_mapping: A mapping of fields in the dataset to their type
        list_field_type_mapping: A mapping of list fields to their contained type
        _dataset_relations:
            A list of named tuples (defined above), containing another DataSet instance, and a field
            for each dataset to join them on.
        _data:
            A list for storage of raw data, not reccomended for direct access,
            as it does not include data from related datasets (use the data property instead)
    """

    def __init__(self, name, json_path: str = None, _parsed_data: dict = None):
        """Load data from either a JSON path, or some previously parsed data.

        In general cases, load from a JSON file. Loading a previously parsed data set
        is intended only for internal use (see filter_by_value).

        Args:
            name (str): A human readable name for the dataset.
            json_path (str, optional): A path to a JSON file to load. Defaults to None.
            _parsed_data (dict, optional): A list of parsed data, used internally to create a subset. Defaults to None.

        Raises:
            DataLoadException: Raised if invalid data is provided.
            DataLoadException: Raised if no data is provided.
            DataLoadException: Raised if both a JSON file and a parsed data set are provided.
        """
        if json_path is not None and _parsed_data is not None:
            raise DataLoadException(
                "DataSet expects data from either a JSON file, or a dictionary (got both)"
            )

        if json_path is None and _parsed_data is None:
            raise DataLoadException(
                "DataSet expects data from either a JSON file, or a dictionary (got neither)"
            )

        if json_path:
            with open(json_path, "r") as json_f:
                self._data = json.load(json_f)
        else:
            self._data = _parsed_data

        if type(self._data) is not list:
            raise DataLoadException(f"Expected list of values (got {type(self._data)})")

        self.name = name
        self.fields = self._get_data_fields()

        if json_path is not None and "_foreign_fields" in self.fields:
            raise DataLoadException("Data contains an illegal field (_foreign_fields)")

        (
            self.field_type_mapping,
            self.list_field_type_mapping,
        ) = self._validate_data_types()

        self._dataset_relations: List[DataSetRelation] = []

    @property
    def data(self) -> List[Dict]:
        """The intended way of accessing the dataset, as it includes joined data from related datasets.

        This method should only be used when inspecting individual records is required, as this will cause all
        records to have their foreign fields loaded from related datasets, which may have a performance impact.


        Returns:
            List[Dict]: The contained dataset, along with any joined fields
        """
        return [self._update_record_with_foreign_data(r) for r in self._data]

    def filter_by_value(self, field: str, value) -> DataSet:
        """Create a filtered subset of the current dataset

        Matches on whole values, or in the case of a list of values, one of the values in the list.

        Args:
            field (str): The field to filter on. Must be a field of the original dataset (not a foreign field).
            value (varies): The value to match on. The type must match the type of the field.

        Raises:
            DataSetException: The type of the field and the type of the value provided do not match.

        Returns:
            DataSet: A new instance of this class containing the filtered dataset.
            This new dataset can be filtered again as required
        """

        field_data_type = self.field_type_mapping[field]
        if (
            field_data_type
            != list  # if it's a list, we're interested in the internal data type
            and value
            is not None  # searching on null values is supported for all data types
            and type(value) != field_data_type
        ):
            raise DataSetException(
                f"Tried to filter on a {field_data_type} field "
                f"({field}) with a {type(value)} value"
            )

        if field_data_type == list:
            new_data_set = DataSet(
                self.name,
                _parsed_data=[
                    record for record in self._data if value in record.get(field, [])
                ],
            )

        else:
            new_data_set = DataSet(
                self.name,
                _parsed_data=[
                    record for record in self._data if record.get(field) == value
                ],
            )

        # this is too fiddly to be set in the constructor, so just do it here
        # when the filtered set is created
        new_data_set._dataset_relations = self._dataset_relations

        return new_data_set

    def relate_dataset(self, other_dataset: DataSet, field: str, foreign_field: str):
        """Relates (joins) the current dataset to another dataset on a given field.

        Args:
            other_dataset (DataSet): Other (foreign) dataset to join
            field (str): Field on this dataset to join
            foreign_field (str): Field on the foreign data to join

        Raises:
            DataSetException: There is another dataset already related to this one with
            the same name as the provided other dataset.
        """
        if any(
            relation.foreign_data_set.name == other_dataset.name
            for relation in self._dataset_relations
        ):
            raise DataSetException(
                "Tried to add a relation to a dataset with a name "
                f"that is already related to this one ({other_dataset.name})"
            )
        self._dataset_relations.append(
            DataSetRelation(other_dataset, field, foreign_field)
        )

    def _update_record_with_foreign_data(self, record: Dict) -> Dict:
        """Updates a single record in the DataSet with foreign fields.

        Adds a field "_foreign_fields" to the record when there are matching foreign data records.
        This field is a dictionary, with keys being the name of the foreign dataset, and values being
        lists of the records attached to the foreign data set.

        Args:
            record (Dict): The individual record to process.

        Returns:
            Dict: The record, with an additional "_foreign_fields" key if required
        """
        if "_foreign_fields" in record.keys() or not self._dataset_relations:
            return record

        foreign_fields = defaultdict(list)
        for relation in self._dataset_relations:
            foreign_records = [
                r
                for r in relation.foreign_data_set._data
                if record.get(relation.field) == r.get(relation.foreign_field)
            ]

            if foreign_records:
                foreign_fields[relation.foreign_data_set.name].extend(foreign_records)

        if foreign_records:
            record["_foreign_fields"] = foreign_fields

        return record

    def _validate_data_types(self) -> Tuple[Dict, Dict]:
        """Validate that each field in the dataset has a static data type.

        If a list is provided, also validate that each item in the list.

        Raises:
            DataLoadException: If field contains a mixed data type.
            DataLoadException: If a list field contains a mixed data type.

        Returns:
            Tuple[Dict, Dict]: A dict mapping fields to their data types.
            and a dict mapping list type fields to the list's contained data type.
        """
        field_mapping = {}
        list_field_mapping = {}

        for field in self.fields:
            value_types = {
                type(record.get(field))
                for record in self._data
                if type(record.get(field)) != type(None)
            }

            if len(value_types) > 1:
                data_types = ", ".join([str(x) for x in value_types])
                raise DataLoadException(
                    f"Data contains a field ({field}) that has mixed data types ({data_types})"
                )

            if len(value_types) == 0:
                raise DataLoadException(
                    f"Data contains a field ({field}) that has entirely null values"
                )

            field_data_type = value_types.pop()

            if field_data_type == dict:
                raise DataLoadException(
                    f"Data contains a field ({field}) that has objects"
                )

            if field_data_type == list:
                # if there is a list field, all records should have the same data type
                # contained within the list

                types_in_list = set()
                for record in self._data:
                    types_in_list.update([type(entry) for entry in record[field]])

                if len(types_in_list) != 1:
                    list_data_types = ", ".join([str(x) for x in types_in_list])
                    raise DataLoadException(
                        f"Data contains a list field ({field}) that "
                        f"contains mixed data types ({list_data_types})"
                    )

                list_field_mapping[field] = types_in_list.pop()

            field_mapping[field] = field_data_type
        return field_mapping, list_field_mapping

    def _get_data_fields(self) -> List[str]:
        """Get fields of the contained data.

        Returns:
            List[str]: Sorted list of all fields in the data
        """
        fields = set()
        for record in self._data:
            fields.update(record.keys())

        return sorted(fields)

    def __len__(self):
        return len(self._data)
