from src.dataset import DataSet, DataLoadException
from src.cli_client import CLIClient

from typing import List
from click.exceptions import Abort


def main():
    # create DataSet objects from JSON files
    tickets_data_set = DataSet("Tickets", json_path="data/tickets.json")
    users_data_set = DataSet("Users", json_path="data/users.json")

    # relate DataSets to each other on "assignee_id"
    tickets_data_set.relate_dataset(users_data_set, "assignee_id", "_id")
    users_data_set.relate_dataset(tickets_data_set, "_id", "assignee_id")

    # initialise client for dealing with CLI interactions
    client = CLIClient([tickets_data_set, users_data_set])

    # clear the console before starting
    client.flush_screen()

    response = client.format_question(
        "Welcome to Zendesk Search!\n"
        "\tOptions:\n"
        "\t\t- 1 to search Zendesk\n"
        "\t\t- 2 to view a list of searchable fields\n"
        "\t\t (press ctrl + c to exit at any time)\n",
        options=["1", "2"],
    )

    if response == "1":
        data_set_names = [data_set.name for data_set in client.data_sets]

        # Get user to select from list of loaded datasets
        selected_data_set = client.data_set_name_mapping[
            client.format_question("Please select data set", options=data_set_names)
        ]

        # Get user to select from list of selected dataset's fields
        selected_search_field = client.format_question(
            "Please select search field", options=selected_data_set.fields
        )

        client.flush_screen()

        # Get user to select if they would like to enter a value, or search for null values
        search_for_none = (
            client.format_question(
                f"Searching {selected_data_set.name} on the {selected_search_field} field\n"
                "\tOptions:\n"
                "\t\t- 1 to enter a search term\n"
                "\t\t- 2 to search for null values\n",
                options=["1", "2"],
            )
            == "2"
        )

        if search_for_none:
            subset = selected_data_set.filter_by_value(selected_search_field, None)

        else:  # i.e., search for a value
            # get the data type of the field, and then ask the user to enter the data type
            field_type = selected_data_set.field_type_mapping[selected_search_field]

            if field_type == str:
                search_text = client.format_question(
                    "Please enter search text", response_type=str
                )
                subset = selected_data_set.filter_by_value(
                    selected_search_field, search_text
                )

            elif field_type == bool:
                search_option = client.format_question(
                    "Please enter true/false", response_type=bool
                )

                subset = selected_data_set.filter_by_value(
                    selected_search_field, search_option
                )

            elif field_type in (int, float):
                search_option = client.format_question(
                    "Please enter number", response_type=field_type
                )
                subset = selected_data_set.filter_by_value(
                    selected_search_field, search_option
                )

            elif field_type == list:
                contained_data_type = selected_data_set.list_field_type_mapping[
                    selected_search_field
                ]
                search_option = client.format_question(
                    f"Please enter {contained_data_type}",
                    response_type=contained_data_type,
                )
                subset = selected_data_set.filter_by_value(
                    selected_search_field, search_option
                )
        client.format_data(subset)

    elif response == "2":
        message = f"\n".join(
            [
                f"{data_set.name} search fields:\n\t" + "\n\t".join(data_set.fields)
                for data_set in client.data_sets
            ]
        )

        client.user_info(message)


if __name__ == "__main__":
    try:
        main()
    except Abort:
        # a KeyboardInterrupt during a click session will be reraised as an Abort
        # catch it here and throw it away, so the user can quit with a keyboard interrupt
        # and not have their stdout polluted by a bogus stacktrace
        pass
