# commons.py
# Author: Thomas MINIER - MIT License 2017-2019
import click
import requests

from json import dumps
from math import inf
from sys import exit


@click.command()
@click.argument("entrypoint")
@click.argument("default_graph_uri")
@click.option(
    "-q", "--query", type=click.STRING, default=None,
    help="SPARQL query to execute (passed in command-line)"
)
@click.option(
    "-f", "--file", type=click.STRING, default=None,
    help="File containing a SPARQL query to execute"
)
@click.option(
    "--format", type=click.Choice(["json", "xml"]), default="json",
    help="Format of the results set, formatted according to W3C SPARQL standards."
)
@click.option(
    "-l", "--limit", type=click.INT, default=None,
    help="Maximum number of solutions bindings to fetch, similar to the SPARQL LIMIT modifier."
)
def sage_query(entrypoint, default_graph_uri, query, file, format, limit):
    """
        Send a SPARQL query to a SaGe server hosted at ENTRYPOINT, with DEFAULT_GRAPH_URI as the default RDF Graph. It does not act as a Smart client, so only queries supported by the server will be evaluated.

        Example usage: sage-query http://sage.univ-nantes.fr/sparql http://sage.univ-nantes.fr/sparql/dbpedia-2016-04 -q "SELECT * WHERE { ?s ?p ?o }"
    """
    # assert that we have a query to evaluate
    if query is None and file is None:
        print("Error: you must specificy a query to execute, either with --query or --file. See sage-query --help for more informations.")
        exit(1)

    if limit is None:
        limit = inf

    # load query from file if required
    if file is not None:
        with open(file) as query_file:
            query = query_file.read()

    # prepare query headers
    headers = {
        "accept": "text/html",
        "content-type": "application/json",
        "next": None
    }
    payload = {
        "query": query,
        "defaultGraph": default_graph_uri
    }

    has_next = True
    count = 0
    while has_next and count < limit:
        response = requests.post(entrypoint, headers=headers, data=dumps(payload))
        json_response = response.json()
        has_next = json_response['next']
        payload['next'] = json_response['next']
        for bindings in json_response['bindings']:
            print(str(bindings))
            count += 1
            if count >= limit:
                break
