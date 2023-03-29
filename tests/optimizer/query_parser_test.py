# query_parser_test.py
# Author: Thomas MINIER - MIT License 2017-2018
import pytest
from sage.query_engine.sage_engine import SageEngine
from sage.query_engine.optimizer.query_parser import parse_query
from sage.database.backends.hdt.connector import HDTFileConnector
from tests.utils import DummyDataset


hdtDoc = HDTFileConnector('tests/data/watdiv.10M.hdt')
dataset = DummyDataset(hdtDoc, 'watdiv100')
engine = SageEngine()

queries = [
    ("""
    SELECT * WHERE {
        ?s <http://schema.org/eligibleRegion> <http://db.uwaterloo.ca/~galuc/wsdbm/Country9> .
        ?s <http://purl.org/goodrelations/includes> ?includes .
        ?s <http://purl.org/goodrelations/validThrough> ?validity .
    }
    """, 2180),
    ("""
    SELECT *
    FROM <http://localhost:8000/sparql/watdiv100>
    WHERE {
        ?s <http://schema.org/eligibleRegion> <http://db.uwaterloo.ca/~galuc/wsdbm/Country9> .
        ?s <http://purl.org/goodrelations/includes> ?includes .
        ?s <http://purl.org/goodrelations/validThrough> ?validity .
    }
    """, 2180),
    ("""
    SELECT * WHERE {
        {
            ?s <http://schema.org/eligibleRegion> <http://db.uwaterloo.ca/~galuc/wsdbm/Country9> .
            ?s <http://purl.org/goodrelations/includes> ?includes .
            ?s <http://purl.org/goodrelations/validThrough> ?validity .
        } UNION {
            ?s <http://schema.org/eligibleRegion> <http://db.uwaterloo.ca/~galuc/wsdbm/Country9> .
            ?s <http://purl.org/goodrelations/includes> ?includes .
            ?s <http://purl.org/goodrelations/validThrough> ?validity .
        }
    }
    """, 2180 * 2),
    ("""
    SELECT * WHERE {
        <http://db.uwaterloo.ca/~galuc/wsdbm/Offer1000> <http://purl.org/goodrelations/price> ?price .
        FILTER(?price = "232")
    }
    """, 1),
    ("""
    SELECT * WHERE {
        <http://db.uwaterloo.ca/~galuc/wsdbm/Offer1000> <http://purl.org/goodrelations/price> ?price .
        FILTER(?price = "232" && 1 + 2 = 3)
    }
    """, 1),
    # ("""
    # SELECT * WHERE {
    #     <http://db.uwaterloo.ca/~galuc/wsdbm/Offer1000> ?p ?o .
    #     FILTER(?p = iri("http://purl.org/goodrelations/price"))
    # }
    # """, 1),
    ("""
    SELECT * WHERE {
        ?s <http://schema.org/eligibleRegion> <http://db.uwaterloo.ca/~galuc/wsdbm/Country9> .
        GRAPH <http://localhost:8000/sparql/watdiv100> {
            ?s <http://purl.org/goodrelations/includes> ?includes .
            ?s <http://purl.org/goodrelations/validThrough> ?validity .
        }
    }
    """, 2180),
    ("""
    SELECT * WHERE {
        ?s ?filter_0 ?state_1_1 .
        FILTER((<http://www.ppbenchmark.com/e7> != ?filter_0) && (<http://www.ppbenchmark.com/e2> != ?filter_0))
    }
    """, 0)
]


class TestQueryParser(object):
    @pytest.mark.asyncio
    @pytest.mark.parametrize("query,cardinality", queries)
    async def test_query_parser(self, query, cardinality):
        context= { 'quantum': 10e7, 'max_results': 10e7, 'start_timestamp': 0 }
        iterator, cards = parse_query(query, dataset, 'watdiv100', context)
        assert len(cards) > 0
        assert iterator is not None
