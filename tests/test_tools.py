"""
tests/test_tools.py
-------------------
Unit tests for all three agent tools.
Run with:  pytest tests/ -v
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Ensure complaints go to a temp dir during tests ───────────────────────────
@pytest.fixture(autouse=True)
def _tmp_complaints_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPLAINTS_DIR", str(tmp_path / "complaints"))
    # Re-import so the module picks up the patched env var
    import importlib
    import tools.complaint as cm
    cm.COMPLAINTS_DIR = Path(os.getenv("COMPLAINTS_DIR"))
    yield


# ─────────────────────────────────────────────────────────────────────────────
# search_flights
# ─────────────────────────────────────────────────────────────────────────────
class TestSearchFlights:
    def _call(self, **kwargs):
        from tools.flight_search import search_flights
        return search_flights.invoke(kwargs)

    def test_returns_flights_for_valid_route(self):
        result = self._call(origin="JFK", destination="LAX", date="2099-01-15")
        assert "FL" in result          # flight ID present
        assert "JFK" in result
        assert "LAX" in result

    def test_invalid_date_format(self):
        result = self._call(origin="JFK", destination="LAX", date="15-01-2099")
        assert "Invalid date format" in result

    def test_past_date_rejected(self):
        result = self._call(origin="JFK", destination="LAX", date="2000-01-01")
        assert "past" in result.lower()

    def test_multiple_passengers(self):
        result = self._call(
            origin="LHR", destination="CDG", date="2099-06-01", passengers=2
        )
        assert "2 passenger" in result

    def test_case_insensitive_airports(self):
        result = self._call(origin="jfk", destination="lax", date="2099-03-20")
        assert "JFK" in result
        assert "LAX" in result


# ─────────────────────────────────────────────────────────────────────────────
# book_flight
# ─────────────────────────────────────────────────────────────────────────────
class TestBookFlight:
    def _call(self, **kwargs):
        from tools.flight_booking import book_flight
        return book_flight.invoke(kwargs)

    def test_successful_booking(self):
        result = self._call(
            flight_id="FL1234",
            passenger_name="Alice Smith",
            date="2099-07-10",
            origin="JFK",
            destination="LAX",
            seat_class="Economy",
            passengers=1,
        )
        assert "Confirmed" in result
        assert "Alice Smith" in result
        assert "PNR" in result

    def test_empty_name_rejected(self):
        result = self._call(
            flight_id="FL9999",
            passenger_name="",
            date="2099-07-10",
            origin="JFK",
            destination="LAX",
        )
        assert "empty" in result.lower() or "required" in result.lower()

    def test_business_class_more_expensive_than_economy(self):
        from tools.flight_booking import book_flight
        eco = book_flight.invoke(dict(
            flight_id="FL5555", passenger_name="Bob", date="2099-08-01",
            origin="A", destination="B", seat_class="Economy", passengers=1,
        ))
        biz = book_flight.invoke(dict(
            flight_id="FL5555", passenger_name="Bob", date="2099-08-01",
            origin="A", destination="B", seat_class="Business", passengers=1,
        ))
        # Extract prices (both contain "$ X.XX")
        import re
        eco_price = float(re.search(r"\$(\d+\.\d+)", eco).group(1))
        biz_price = float(re.search(r"\$(\d+\.\d+)", biz).group(1))
        assert biz_price > eco_price


# ─────────────────────────────────────────────────────────────────────────────
# get_booking
# ─────────────────────────────────────────────────────────────────────────────
class TestGetBooking:
    def test_retrieve_after_booking(self):
        from tools.flight_booking import book_flight, get_booking
        import re

        confirm = book_flight.invoke(dict(
            flight_id="FL0001",
            passenger_name="Carol White",
            date="2099-09-09",
            origin="SYD",
            destination="SIN",
            seat_class="First",
            passengers=1,
        ))
        pnr = re.search(r"PNR\s+\*\*([A-Z0-9]{6})\*\*", confirm).group(1)
        details = get_booking.invoke({"pnr": pnr})
        assert "Carol White" in details
        assert "SYD" in details

    def test_unknown_pnr_returns_error(self):
        from tools.flight_booking import get_booking
        result = get_booking.invoke({"pnr": "ZZZZZZ"})
        assert "No booking found" in result


# ─────────────────────────────────────────────────────────────────────────────
# file_complaint
# ─────────────────────────────────────────────────────────────────────────────
class TestFileComplaint:
    def _call(self, **kwargs):
        from tools.complaint import file_complaint
        return file_complaint.invoke(kwargs)

    def test_creates_txt_file(self, tmp_path, monkeypatch):
        from tools import complaint as cm
        cm.COMPLAINTS_DIR = tmp_path / "complaints"

        result = self._call(
            passenger_name="Dave Jones",
            complaint_category="Delay",
            complaint_text="My flight was delayed by 5 hours with no notification.",
            booking_reference="AB1234",
        )

        assert "filed successfully" in result.lower()
        files = list(cm.COMPLAINTS_DIR.glob("complaint_*.txt"))
        assert len(files) == 1

        content = files[0].read_text()
        assert "Dave Jones" in content
        assert "Delay" in content
        assert "AB1234" in content

    def test_empty_name_rejected(self):
        result = self._call(
            passenger_name="",
            complaint_category="Baggage",
            complaint_text="Lost luggage.",
        )
        assert "required" in result.lower() or "empty" in result.lower()

    def test_empty_text_rejected(self):
        result = self._call(
            passenger_name="Eva Green",
            complaint_category="Service",
            complaint_text="",
        )
        assert "empty" in result.lower()

    def test_complaint_id_in_response(self):
        result = self._call(
            passenger_name="Frank Lee",
            complaint_category="Refund",
            complaint_text="I was refused a refund for a cancelled flight.",
        )
        import re
        assert re.search(r"Complaint ID\s*:\s*[A-F0-9]{8}", result)