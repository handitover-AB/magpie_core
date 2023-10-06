"""Unit tests for the Event store.

Will indirectly test relevant parts of the TSDataStore class as well.
"""
import datetime
import pytest

from app.eventstore import TSEventStore, Event


DATA_1 = {"apa": 1, "bepa": 2}
DATA_2 = {"apa": 10, "bepa": 20, "cepa": 30}
DATA_3 = {"apa": 11}


@pytest.fixture
def eventstore():
    store = TSEventStore()
    store.append("TEST_EVENT", DATA_1)
    store.append("TEST_EVENT", DATA_2)
    store.append("ANOTHER_EVENT", DATA_3)
    return store


def test_eventstore_properties(eventstore: TSEventStore):
    assert len(eventstore) == 3
    assert isinstance(eventstore[0], Event)
    assert isinstance(eventstore[1], Event)
    assert isinstance(eventstore[2], Event)
    assert isinstance(eventstore[-1], Event)
    with pytest.raises(IndexError):
        _ = eventstore[3]
    with pytest.raises(TypeError):
        _ = eventstore["apa"]


def test_eventstore_match_multiple(eventstore: TSEventStore):
    matching_events = eventstore.match("TEST_.*")
    assert len(matching_events) == 2
    assert isinstance(matching_events, list)
    assert matching_events[0].data == DATA_1
    assert matching_events[1].data == DATA_2


def test_eventstore_match_single(eventstore: TSEventStore):
    matching_events = eventstore.match("ANOTHER_EVENT")
    assert len(matching_events) == 1
    assert isinstance(matching_events, list)
    assert matching_events[0].data == DATA_3


def test_event_has_timestamp(eventstore: TSEventStore):
    # ARRANGE
    matching_events = eventstore.match("ANOTHER_EVENT")
    string_representation = str(matching_events[0])
    _, name, str_data = string_representation.split(",")
    # TODO: Check correctness of timestamp

    assert len(matching_events) == 1
    assert name == '"ANOTHER_EVENT"'
    assert str_data == f'"{str(DATA_3)}"'


def test_eventstore_with_string_data():
    store = TSEventStore()
    store.append("TEST_EVENT", "test data")
    matching_events = store.match("TEST_EVENT")
    assert len(matching_events) == 1
    assert isinstance(matching_events, list)
    assert isinstance(matching_events[0], Event)
    assert matching_events[0].data == "test data"


def test_eventstore_filter(eventstore: TSEventStore):
    bepa_events = eventstore.match(
        event_name=".*", data_filter_fn=lambda item: item.data.get("bepa") == 20
    )

    cepa_events = eventstore.match(
        event_name="TEST_.*",
        data_filter_fn=lambda item: item.data.get("cepa") is not None,
    )

    assert len(bepa_events) == 1
    assert len(cepa_events) == 1
    assert bepa_events[0].data == DATA_2
    assert cepa_events[0].data == DATA_2


def test_eventstore_filter_negative_tests(eventstore: TSEventStore):
    cepa_events = eventstore.match(
        event_name="ANOTHER_.*",
        data_filter_fn=lambda item: item.data.get("cepa") is not None,
    )

    assert len(cepa_events) == 0


def test_eventstore_wait_for_event(eventstore: TSEventStore):
    # ARRANGE
    # Append an event to the event store:
    eventstore.append("YET_ANOTHER_EVENT", {"foo": "bar"})

    # For testing: simulate that the event appears in one
    # second from now (its timestamp must be later than the
    # time when we begin looking for the event)
    now = datetime.datetime.now()
    delta_t = datetime.timedelta(seconds=1)
    eventstore[-1:][0].timestamp = now + delta_t

    # ACT
    result = eventstore.wait_for_event("YET_ANOTHER_EVENT")

    # ASSERT
    assert result.name == "YET_ANOTHER_EVENT"
    assert result.data == {"foo": "bar"}


def test_pop_is_not_allowed(eventstore: TSEventStore):
    with pytest.raises(TypeError):
        eventstore.pop()


def test_delete_is_not_allowed(eventstore: TSEventStore):
    with pytest.raises(TypeError):
        del eventstore._data[1]  # pylint: disable=protected-access
