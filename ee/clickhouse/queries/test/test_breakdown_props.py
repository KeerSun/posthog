from uuid import uuid4

from freezegun import freeze_time

from ee.clickhouse.models.event import create_event
from ee.clickhouse.queries.breakdown_props import get_breakdown_person_prop_values
from ee.clickhouse.util import ClickhouseTestMixin
from posthog.models.entity import Entity
from posthog.models.filters import Filter
from posthog.models.person import Person
from posthog.test.base import APIBaseTest


def _create_event(**kwargs):
    kwargs.update({"event_uuid": uuid4()})
    create_event(**kwargs)


class TestBreakdownProps(ClickhouseTestMixin, APIBaseTest):
    def test_breakdown_person_props(self):
        p1 = Person.objects.create(team_id=self.team.pk, distinct_ids=["p1"], properties={"$browser": "test"})
        _create_event(
            team=self.team,
            event="$pageview",
            distinct_id="p1",
            timestamp="2020-01-02T12:00:00Z",
            properties={"key": "val"},
        )

        self.team.test_account_filters = [
            {"key": "email", "type": "person", "value": "posthog.com", "operator": "not_icontains"},
            {
                "key": "$host",
                "type": "event",
                "value": ["127.0.0.1:3000", "127.0.0.1:5000", "localhost:5000", "localhost:8000"],
                "operator": "is_not",
            },
            {"key": "distinct_id", "type": "event", "value": "posthog.com", "operator": "not_icontains"},
        ]
        self.team.save()
        with freeze_time("2020-01-04T13:01:01Z"):
            filter = Filter(
                data={
                    "insight": "FUNNELS",
                    "properties": [],
                    "filter_test_accounts": True,
                    "events": [{"id": "$pageview", "name": "$pageview", "type": "events", "order": 0}],
                    "actions": [],
                    "funnel_viz_type": "steps",
                    "display": "FunnelViz",
                    "interval": "day",
                    "breakdown": "$browser",
                    "breakdown_type": "person",
                    "date_from": "-14d",
                    "funnel_window_days": 14,
                }
            )
            res = get_breakdown_person_prop_values(
                filter, Entity({"id": "$pageview", "type": "events"}), "count(*)", self.team.pk, 5
            )
            self.assertEqual(res, ["test"])
