from contextlib import contextmanager
from typing import List
from unittest.mock import patch

from clickhouse_driver.errors import ServerException
from django.db import DEFAULT_DB_ALIAS

from ee.clickhouse.client import sync_execute
from ee.clickhouse.sql.cohort import CREATE_COHORTPEOPLE_TABLE_SQL, DROP_COHORTPEOPLE_TABLE_SQL
from ee.clickhouse.sql.events import DROP_EVENTS_TABLE_SQL, EVENTS_TABLE_SQL
from ee.clickhouse.sql.person import (
    DROP_PERSON_DISTINCT_ID_TABLE_SQL,
    DROP_PERSON_STATIC_COHORT_TABLE_SQL,
    DROP_PERSON_TABLE_SQL,
    PERSON_STATIC_COHORT_TABLE_SQL,
    PERSONS_DISTINCT_ID_TABLE_SQL,
    PERSONS_TABLE_SQL,
)
from ee.clickhouse.sql.session_recording_events import (
    DROP_SESSION_RECORDING_EVENTS_TABLE_SQL,
    SESSION_RECORDING_EVENTS_TABLE_SQL,
)


class ClickhouseTestMixin:
    RUN_MATERIALIZED_COLUMN_TESTS = True

    def tearDown(self):
        try:
            self._destroy_event_tables()
            self._destroy_person_tables()
            self._destroy_session_recording_tables()
            self._destroy_cohortpeople_table()
        except ServerException as e:
            print(e)
            pass

        try:
            self._create_event_tables()
            self._create_person_tables()
            self._create_session_recording_tables()
            self._create_cohortpeople_table()
        except ServerException as e:
            print(e)
            pass

    def _destroy_person_tables(self):
        sync_execute(DROP_PERSON_TABLE_SQL)
        sync_execute(DROP_PERSON_DISTINCT_ID_TABLE_SQL)
        sync_execute(DROP_PERSON_STATIC_COHORT_TABLE_SQL)

    def _create_person_tables(self):
        sync_execute(PERSONS_TABLE_SQL)
        sync_execute(PERSONS_DISTINCT_ID_TABLE_SQL)
        sync_execute(PERSON_STATIC_COHORT_TABLE_SQL)

    def _destroy_session_recording_tables(self):
        sync_execute(DROP_SESSION_RECORDING_EVENTS_TABLE_SQL)

    def _create_session_recording_tables(self):
        sync_execute(SESSION_RECORDING_EVENTS_TABLE_SQL)

    def _destroy_event_tables(self):
        sync_execute(DROP_EVENTS_TABLE_SQL)

    def _create_event_tables(self):
        sync_execute(EVENTS_TABLE_SQL)

    def _destroy_cohortpeople_table(self):
        sync_execute(DROP_COHORTPEOPLE_TABLE_SQL)

    def _create_cohortpeople_table(self):
        sync_execute(CREATE_COHORTPEOPLE_TABLE_SQL)

    @contextmanager
    def _assertNumQueries(self, func):
        yield

    # Ignore assertNumQueries in clickhouse tests
    def assertNumQueries(self, num, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
        return self._assertNumQueries(func)

    @contextmanager
    def capture_select_queries(self):
        from ee.clickhouse.client import _annotate_tagged_query

        sqls: List[str] = []

        def wrapped_method(*args):
            if args[0].strip().startswith("SELECT"):
                sqls.append(args[0])
            return _annotate_tagged_query(*args)

        with patch("ee.clickhouse.client._annotate_tagged_query", wraps=wrapped_method) as wrapped_annotate:
            yield sqls
