# postgre_backend_test.py
# Author: Thomas MINIER - MIT License 2017-2019
import pytest
from sage.database.backends.postgres.connector import PostgresConnector
from tests.database.fixtures import index_scan_fixtures

DB_NAME = 'watdiv'


def assert_next_triple(iterator, expected):
    triple = next(iterator)
    assert triple in expected
    expected.remove(triple)

@pytest.mark.skip(reason="By default, this test is disabled. The database must be created and data loaded before enabling it.")
# @pytest.mark.parametrize("subj,pred,obj,expected", index_scan_fixtures())
def test_postgre_simple_scan(subj, pred, obj, expected):
    with PostgresConnector(DB_NAME, 'sage', 'sage', '') as backend:
        iterator, c = backend.search(subj, pred, obj)
        assert iterator.has_next()
        while iterator.has_next() and len(expected) > 0:
            assert_next_triple(iterator, expected)
        assert not iterator.has_next()
        assert len(expected) == 0


@pytest.mark.skip(reason="By default, this test is disabled. The database must be created and data loaded before enabling it.")
# @pytest.mark.parametrize("subj,pred,obj,expected", index_scan_fixtures())
def test_postgre_resume_scan(subj, pred, obj, expected):
    # don't test for scan that yield one matching RDF triple
    if len(expected) > 1:
        with PostgresConnector(DB_NAME, 'sage', 'sage', '') as backend:
            iterator, c = backend.search(subj, pred, obj)
            assert iterator.has_next()
            # read first triple, then stop and reload a new iterator
            assert_next_triple(iterator, expected)
            last_read = iterator.last_read()
            iterator, c = backend.search(subj, pred, obj, last_read=last_read)
            while iterator.has_next() and len(expected) > 0:
                assert_next_triple(iterator, expected)
            assert not iterator.has_next()
            assert len(expected) == 0


@pytest.mark.skip(reason="By default, this test is disabled. The database must be created and data loaded before enabling it.")
def test_postgre_scan_unknown_pattern():
    with PostgresConnector(DB_NAME, 'sage', 'sage', '') as backend:
        iterator, c = backend.search('http://example.org#toto', None, None)
        assert not iterator.has_next()
        assert next(iterator) is None
