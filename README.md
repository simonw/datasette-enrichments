# datasette-enrichments

[![PyPI](https://img.shields.io/pypi/v/datasette-enrichments.svg)](https://pypi.org/project/datasette-enrichments/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-enrichments?include_prereleases&label=changelog)](https://github.com/simonw/datasette-enrichments/releases)
[![Tests](https://github.com/simonw/datasette-enrichments/workflows/Test/badge.svg)](https://github.com/simonw/datasette-enrichments/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-enrichments/blob/main/LICENSE)

Tools for running enrichments against data stored in Datasette

## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-enrichments

## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-enrichments
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest