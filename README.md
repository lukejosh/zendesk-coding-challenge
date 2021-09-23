# JSON Searcher

A command line interface written in Python to query structured JSON datasets. This was written for the Zendesk coding challenge, which required a command line application be written that is capable of querying two provided datasets. To do that, an application was developed that broadly does the following:

- Implements a `DataSet` class that is capable of parsing, storing and filtering arbitrary structured JSON data. This class is also capable of being joined to another instance of the same type, given there is a field to link the two datasets together.
- Implement a `CLIClient` class to handle user interaction with the program.

## Installation

Requires Python 3.9 (I reccomended [pyenv](https://github.com/pyenv/pyenv) to manage multiple Python versions, but to each their own)

Use [pipenv](https://pipenv.pypa.io/en/latest/) to create a virtual environment and install all dependencies

```bash
cd zendesk-coding-challenge
pipenv install --dev
```

(the `--dev` flag is only required if you intend to run tests)

## Tests

Tests are run through [pytest](https://docs.pytest.org/en/latest/). Pytest will already have been installed by pipenv above; so getting them running is as easy as

```bash
pipenv run pytest
```

## Usage

The script is accessed through `main.py`, and must be run in the environment setup above.

```bash
pipenv run python main.py
```
After running the above, you should be greeted by the CLI!

## Assumptions & Tradeoffs
For the purpose of this coding challenge, a number of assumptions were made:
- The data within a provided JSON dataset must contain an array of objects.
- The data type of a field across the dataset must be consistent (with the exception of `null`). This is to ensure that the input from a user is unambiguous - i.e., if a dataset had some values with `{"age": 24}` and others with `{"age": "24"}`, it becomes difficult to interpret whether the user is interested in an integer or a string, without implementing additional parsing of user input.
- Entries that do not have a field that other entries have will be treated as having a `null` value for that field.
- All JSON data types with the exception of objects (i.e., integers, floats, strings, booleans, arrays, and null) are supported as queryable fields.
- Nulls are supported only for missing data. A field that contains entirely null values is not supported.
- When searching on an array field, any entry that has the search value within it's array will be matched. 
- Searching is only supported on a datasets own fields (i.e., the Tickets dataset can not be filtered down based on the name of the assigned User)