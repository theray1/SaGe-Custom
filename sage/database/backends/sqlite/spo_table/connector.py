import json
import logging
import coloredlogs

from datetime import datetime
from typing import Optional, Tuple

from sage.database.backends.db_iterator import EmptyIterator
from sage.database.backends.sqlite.connector import SQliteConnector
from sage.database.backends.sqlite.spo_table.iterator import SQliteIterator
from sage.database.backends.sqlite.spo_table.queries import get_start_query, get_resume_query
from sage.database.backends.sqlite.spo_table.queries import get_insert_query, get_delete_query

coloredlogs.install(level='INFO', fmt='%(asctime)s - %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


class DefaultSQliteConnector(SQliteConnector):
    """
        A DefaultSQliteConnector search for RDF triples in a SQlite database where triples are stored in one SQL table.
        Constructor arguments:
            - table_name `str`: Name of the SQL table containing RDF data.
            - database `str`: the name of the sqlite database file.
            - fetch_size `int`: how many RDF triples are fetched per SQL query (default to 500)
    """

    def __init__(self, table_name: str, database: str, fetch_size: int = 500):
        super(DefaultSQliteConnector, self).__init__(table_name, database, fetch_size)

    def search(self, subject: str, predicate: str, obj: str, last_read: Optional[str] = None, as_of: Optional[datetime] = None) -> Tuple[SQliteIterator, int]:
        """
            Get an iterator over all RDF triples matching a triple pattern.
            Args:
                - subject ``string`` - Subject of the triple pattern
                - predicate ``string`` - Predicate of the triple pattern
                - obj ``string`` - Object of the triple pattern
                - last_read ``string=None`` ``optional`` -  OFFSET ID used to resume scan
                - as_of ``datetime=None`` ``optional`` - Perform all reads against a consistent snapshot represented by a timestamp.
            Returns:
                A tuple (`iterator`, `cardinality`), where `iterator` is a Python iterator over RDF triples matching the given triples pattern, and `cardinality` is the estimated cardinality of the triple pattern
        """
        # do warmup if necessary
        self.open()

        # format triple patterns for the SQlite API
        subject = subject if (subject is not None) and (not subject.startswith('?')) else None
        predicate = predicate if (predicate is not None) and (not predicate.startswith('?')) else None
        obj = obj if (obj is not None) and (not obj.startswith('?')) else None
        pattern = {'subject': subject, 'predicate': predicate, 'object': obj}

        # dedicated cursor used to scan this triple pattern
        # WARNING: we need to use a dedicated cursor per triple pattern iterator.
        # Otherwise, we might reset a cursor whose results were not fully consumed.
        cursor = self._manager.get_connection().cursor()

        # create a SQL query to start a new index scan
        if last_read is None:
            start_query, start_params = get_start_query(subject, predicate, obj, self._table_name)
        else:
            # empty last_read key => the scan has already been completed
            if len(last_read) == 0:
                return EmptyIterator(pattern), 0
            # otherwise, create a SQL query to resume the index scan
            last_read = json.loads(last_read)
            t = (last_read["s"], last_read["p"], last_read["o"])
            start_query, start_params = get_resume_query(subject, predicate, obj, t, self._table_name)

        # create the iterator to yield the matching RDF triples
        iterator = SQliteIterator(
            cursor, self._manager.get_connection(),
            start_query, start_params,
            self._table_name,
            pattern,
            fetch_size=self._fetch_size)
        card = self._estimate_cardinality(subject, predicate, obj)
        return iterator, card

    def from_config(config: dict) -> SQliteConnector:
        """Build a SQliteConnector from a configuration object"""
        if 'database' not in config:
            raise SyntaxError(
                'A valid configuration for a SQlite connector must contains the database file')

        table_name = config['name']
        database = config['database']
        fetch_size = config['fetch_size'] if 'fetch_size' in config else 500

        return DefaultSQliteConnector(table_name, database, fetch_size=fetch_size)

    def insert(self, subject: str, predicate: str, obj: str) -> None:
        """
            Insert a RDF triple into the RDF Graph.
        """
        # do warmup if necessary, then start a new transaction
        self.open()
        transaction = self._manager.start_transaction()
        if subject is not None and predicate is not None and obj is not None:
            insert_query = get_insert_query(self._table_name)
            transaction.execute(insert_query, (subject, predicate, obj))
            self._manager.commit()

    def delete(self, subject: str, predicate: str, obj: str) -> None:
        """
            Delete a RDF triple from the RDF Graph.
        """
        # do warmup if necessary, then start a new transaction
        self.open()
        transaction = self._manager.start_transaction()
        if subject is not None and predicate is not None and obj is not None:
            delete_query = get_delete_query(self._table_name)
            transaction.execute(delete_query, (subject, predicate, obj))
            self._manager.commit()
