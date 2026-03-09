"""
tools/flight_search.py
----------------------
Tool: search_flights
Simulates querying a flight-availability API.
Returns dummy data so the agent can reason about available options.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

from langchain.tools import tool


# ── Dummy airline / route data ────────────────────────────────────────────────
_AIRLINES = ["SkyWings", "AeroJet", "CloudHop", "PeakAir", "NorthStar"]
_AIRCRAFT = ["Boeing 737", "Airbus A320", "Boeing 787", "Airbus A350"]


def _build_dummy_flights(
    origin: str, destination: str, date: str, num_results: int = 3
) -> list[dict]:
    """Generate a list of plausible-looking dummy flights."""
    random.seed(f"{origin}{destination}{date}")  # deterministic per query
    flights = []
    for i in range(num_results):
        dep_hour = random.randint(6, 20)
        dep_min = random.choice([0, 15, 30, 45])
        duration_h = random.randint(1, 12)
        price = round(random.uniform(80, 900), 2)

        dep_time = f"{dep_hour:02d}:{dep_min:02d}"
        arr_hour = (dep_hour + duration_h) % 24
        arr_time = f"{arr_hour:02d}:{dep_min:02d}"

        flights.append(
            {
                "flight_id": f"FL{random.randint(1000, 9999)}",
                "airline": random.choice(_AIRLINES),
                "aircraft": random.choice(_AIRCRAFT),
                "origin": origin.upper(),
                "destination": destination.upper(),
                "date": date,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration_hours": duration_h,
                "price_usd": price,
                "seats_available": random.randint(1, 50),
                "class": random.choice(["Economy", "Business", "First"]),
            }
        )
    return sorted(flights, key=lambda f: f["price_usd"])


# ── LangChain Tool ────────────────────────────────────────────────────────────


@tool
def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: Optional[int] = 1,
) -> str:
    """Search for available flights between two airports on a specific date.

    Args:
        origin:      IATA code or city name of the departure airport (e.g. 'JFK', 'London').
        destination: IATA code or city name of the arrival airport (e.g. 'LAX', 'Paris').
        date:        Travel date in YYYY-MM-DD format.
        passengers:  Number of passengers (default 1).

    Returns:
        A formatted string listing available flights or a 'no flights' message.
    """
    # ── Basic date validation ──────────────────────────────────────────────────
    try:
        travel_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return (
            f"❌ Invalid date format '{date}'. Please use YYYY-MM-DD "
            "(e.g. 2025-06-15)."
        )

    if travel_date.date() < datetime.today().date():
        return f"❌ The date {date} is in the past. Please choose a future date."

    flights = _build_dummy_flights(origin, destination, date)

    # Filter by seat availability
    available = [f for f in flights if f["seats_available"] >= (passengers or 1)]

    if not available:
        return (
            f"No flights found from {origin.upper()} to {destination.upper()} "
            f"on {date} for {passengers} passenger(s)."
        )

    lines = [
        f"✈️  Flights from {origin.upper()} → {destination.upper()} on {date} "
        f"({passengers} passenger(s)):\n"
    ]
    for f in available:
        lines.append(
            f"  🔹 {f['flight_id']} | {f['airline']} | {f['aircraft']}\n"
            f"     Departs {f['departure_time']} → Arrives {f['arrival_time']} "
            f"({f['duration_hours']}h)\n"
            f"     Class: {f['class']} | Price: ${f['price_usd']:.2f} | "
            f"Seats: {f['seats_available']}\n"
        )

    return "\n".join(lines)