import click
from src.dataset import DataSet
from typing import List


class CLIException(Exception):
    pass


class CLIClient:
    """A CLI client to allow for a user to interact with a DataSet

    Allows for a user to provide input, and allows for the formatting of DataSets for user viewing
    """

    def __init__(self, data_sets: List[DataSet]):
        self.data_sets = data_sets
        self.data_set_name_mapping = {
            data_set.name: data_set for data_set in self.data_sets
        }

    def format_question(
        self, question: str, response_type: type = None, options: List = None
    ):
        """Receive input from the user.

        Given some prompt to the user, receive a response back in an optionally specified data type
        or from an optionally supplied list.

        Args:
            question (str): Prompt to be provided to the user
            response_type (type, optional):
                The type of response expected (int, str, bool).
                If response type is not specified, it will be inferred from the options provided.

            options (List, optional): A list of options for the user to select from. Defaults to None.

        Raises:
            CLIException: Neither response_type or options were provided
            CLIException: Both response_type and options were provided

        Returns:
            Any: Response from the user, in the type requested either in the response_type, or in the options
        """
        if response_type is None and options is None:
            raise CLIException(
                "Must specify either the response type, or valid options (got neither)"
            )

        if response_type is not None and options is not None:
            raise CLIException(
                "Must specify either the response type, or valid options (got both)"
            )

        if options:
            return click.prompt(question, type=click.Choice(options, case_sensitive=False))

        else:
            return click.prompt(question, type=response_type)

    def _format_rows_own_data(self, row: dict, fields: List[str]) -> str:
        """Create a formatted string containing a single row of a DataSet's own data (not foreign fields)

        This requires the fields of the dataset to be provided as well, so that a field that is
        not provided for a particular row can still be displayed as None.

        Args:
            row (dict): Individual row (from a DataSet's data property) to be formatted
            fields (List[str]): List of fields of the dataset

        Returns:
            str: Formatted string, each field/value on it's own line and tab separated
        """
        return "\n".join([f"{field}\t{row.get(field)}" for field in fields])

    def _format_rows_foreign_data(self, foreign_data: dict) -> str:
        """Create a formatted string containing a single row of a DataSet's foreign data (not it's own fields)

        Args:
            foreign_data (dict): Individual row (from a DataSet's data property) to be formatted
            fields (List[str]): List of fields of the dataset

        Returns:
            str: Formatted string, each field/value on it's own line and tab separated
        """
        formatted_data = ""

        for foreign_data_set_name, foreign_rows in foreign_data.items():
            formatted_data += "\n" + foreign_data_set_name
            for foreign_row in foreign_rows:
                formatted_data += "\n\t__________"
                for field, value in foreign_row.items():
                    formatted_data += f"\n\t{field}\t{value}"

        return formatted_data

    def format_data(self, data_set: DataSet):
        """Creates a formatted string for a dataset ready for presentation to a user.

        Aggregate of the dataset's own data and foreign fields.

        Args:
            data_set (DataSet): dataset to format
        """
        # this data is data that "belongs" to the dataset

        if len(data_set) == 0:
            formatted_data = "No results returned"

        else:
            formatted_entries = []
            
            for entry in data_set.data:
                formatted_entry = ""
                formatted_entry += self._format_rows_own_data(entry, data_set.fields)

                if "_foreign_fields" in entry.keys():
                    formatted_entry += self._format_rows_foreign_data(
                        entry["_foreign_fields"]
                    )

                formatted_entries.append(formatted_entry)
            
            formatted_data = "\n\n".join(formatted_entries)

        # this function returns None, however, return it here so we can intercept
        # the result while testing
        return click.echo(formatted_data)

    def user_info(self, info: str):
        """Prints information to the user's screen

        Args:
            info (str): String to present
        """
        click.echo(info)

    def flush_screen(self):
        """Flushes terminal window"""
        click.clear()
