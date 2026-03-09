"""
tools/flight_booking.py
-----------------------
Tool: book_flight
Simulates booking a flight and returns a confirmation record.
"""

from __future__ import annotations

import random
import string
import uuid
from datetime import datetime
from typing import Optional

from langchain.tools import tool


# ── In-memory booking ledger (persists for the lifetime of the process) ───────
_BOOKINGS: dict[str, dict] = {}


def _generate_pnr() -> str:
    """Generate a 6-character alphanumeric PNR (Passenger Name Record)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ── LangChain Tool ────────────────────────────────────────────────────────────


@tool
def book_flight(
    flight_id: str,
    passenger_name: str,
    date: str,
    origin: str,
    destination: str,
    seat_class: Optional[str] = "Economy",
    passengers: Optional[int] = 1,
) -> str:
    """Book a specific flight for a passenger.

    Call this tool ONLY after confirming that the flight exists via search_flights.

    Args:
        flight_id:      The flight identifier returned by search_flights (e.g. 'FL4823').
        passenger_name: Full name of the primary passenger.
        date:           Travel date in YYYY-MM-DD format.
        origin:         Departure airport / city.
        destination:    Arrival airport / city.
        seat_class:     Cabin class – 'Economy', 'Business', or 'First' (default Economy).
        passengers:     Number of seats to book (default 1).

    Returns:
        A booking confirmation with PNR, or an error message.
    """
    if not passenger_name.strip():
        return "❌ Passenger name cannot be empty."

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"❌ Invalid date format '{date}'. Please use YYYY-MM-DD."

    # Simulate price lookup (deterministic per flight_id + class)
    random.seed(flight_id + (seat_class or "Economy"))
    base_price = round(random.uniform(80, 900), 2)
    multiplier = {"Economy": 1.0, "Business": 2.5, "First": 4.0}.get(
        seat_class or "Economy", 1.0
    )
    total_price = round(base_price * multiplier * (passengers or 1), 2)

    pnr = _generate_pnr()
    booking_id = str(uuid.uuid4())[:8].upper()

    record = {
        "booking_id": booking_id,
        "pnr": pnr,
        "flight_id": flight_id,
        "passenger_name": passenger_name,
        "origin": origin.upper(),
        "destination": destination.upper(),
        "date": date,
        "seat_class": seat_class,
        "passengers": passengers,
        "total_price_usd": total_price,
        "status": "CONFIRMED",
        "booked_at": datetime.utcnow().isoformat() + "Z",
    }

    _BOOKINGS[pnr] = record

    return (
        f"✅ Booking Confirmed!\n\n"
        f"  📋 Booking ID : {booking_id}\n"
        f"  🎫 PNR        : {pnr}\n"
        f"  ✈️  Flight     : {flight_id}\n"
        f"  👤 Passenger  : {passenger_name}\n"
        f"  🗓️  Date       : {date}\n"
        f"  📍 Route      : {origin.upper()} → {destination.upper()}\n"
        f"  💺 Class      : {seat_class} × {passengers} seat(s)\n"
        f"  💵 Total      : ${total_price:.2f} USD\n"
        f"  🟢 Status     : CONFIRMED\n\n"
        f"Please save your PNR **{pnr}** for check-in and future reference."
    )


@tool
def get_booking(pnr: str) -> str:
    """Retrieve an existing booking by PNR.

    Args:
        pnr: The 6-character Passenger Name Record returned at booking time.

    Returns:
        Booking details or a not-found message.
    """
    record = _BOOKINGS.get(pnr.upper())
    if not record:
        return f"❌ No booking found for PNR '{pnr.upper()}'."

    return (
        f"📋 Booking Details for PNR {record['pnr']}:\n"
        f"  Flight     : {record['flight_id']}\n"
        f"  Passenger  : {record['passenger_name']}\n"
        f"  Route      : {record['origin']} → {record['destination']}\n"
        f"  Date       : {record['date']}\n"
        f"  Class      : {record['seat_class']} × {record['passengers']} seat(s)\n"
        f"  Total      : ${record['total_price_usd']:.2f} USD\n"
        f"  Status     : {record['status']}\n"
        f"  Booked at  : {record['booked_at']}\n"
    )