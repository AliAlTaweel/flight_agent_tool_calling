"""
tools/complaint.py
------------------
Tool: file_complaint
Accepts a passenger complaint and writes it to a timestamped .txt file
inside the configured complaints directory.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

from langchain.tools import tool

# Directory where complaint files are stored (override via env var)
COMPLAINTS_DIR = Path(os.getenv("COMPLAINTS_DIR", "complaints"))


@tool
def file_complaint(
    passenger_name: str,
    complaint_category: str,
    complaint_text: str,
    booking_reference: str = "",
) -> str:
    """Record a passenger complaint and save it as a .txt file.

    Use this tool whenever a user expresses dissatisfaction, reports a problem,
    or explicitly asks to raise a complaint.

    Args:
        passenger_name:      Full name of the complaining passenger.
        complaint_category:  Category such as 'Delay', 'Baggage', 'Service',
                             'Refund', 'Booking Error', 'Other'.
        complaint_text:      Detailed description of the complaint in the
                             passenger's own words.
        booking_reference:   PNR or booking ID if the complaint relates to a
                             specific booking (leave blank if not applicable).

    Returns:
        Confirmation message with the saved file path and complaint ID.
    """
    if not passenger_name.strip():
        return "❌ Passenger name is required to file a complaint."
    if not complaint_text.strip():
        return "❌ Complaint text cannot be empty."

    # Ensure the complaints directory exists
    COMPLAINTS_DIR.mkdir(parents=True, exist_ok=True)

    complaint_id = str(uuid.uuid4())[:8].upper()
    timestamp = datetime.utcnow()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() else "_" for c in passenger_name)
    filename = f"complaint_{safe_name}_{timestamp_str}_{complaint_id}.txt"
    filepath = COMPLAINTS_DIR / filename

    content = (
        "=" * 60 + "\n"
        "            PASSENGER COMPLAINT RECORD\n"
        "=" * 60 + "\n\n"
        f"Complaint ID       : {complaint_id}\n"
        f"Filed At (UTC)     : {timestamp.isoformat()}Z\n"
        f"Passenger Name     : {passenger_name}\n"
        f"Category           : {complaint_category}\n"
        f"Booking Reference  : {booking_reference if booking_reference else 'N/A'}\n\n"
        "─" * 60 + "\n"
        "COMPLAINT DETAILS:\n"
        "─" * 60 + "\n\n"
        f"{complaint_text.strip()}\n\n"
        "─" * 60 + "\n"
        "STATUS             : RECEIVED – UNDER REVIEW\n"
        "=" * 60 + "\n"
    )

    filepath.write_text(content, encoding="utf-8")

    return (
        f"📝 Complaint filed successfully!\n\n"
        f"  🆔 Complaint ID : {complaint_id}\n"
        f"  👤 Passenger    : {passenger_name}\n"
        f"  🏷️  Category     : {complaint_category}\n"
        f"  📁 Saved to     : {filepath}\n\n"
        f"Your complaint has been recorded and will be reviewed by our team. "
        f"Please keep your Complaint ID **{complaint_id}** for follow-up."
    )