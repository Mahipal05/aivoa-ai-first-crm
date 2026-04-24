from __future__ import annotations

from sqlalchemy.orm import Session

from .models import HCP, Material


HCP_SEED = [
    {
        "name": "Dr. Anita Sharma",
        "specialty": "Cardiology",
        "organization": "Medisphere Heart Institute",
        "city": "Mumbai",
        "territory": "West Zone",
    },
    {
        "name": "Dr. Rajiv Menon",
        "specialty": "Endocrinology",
        "organization": "Apollo Specialty Clinic",
        "city": "Bengaluru",
        "territory": "South Zone",
    },
    {
        "name": "Dr. Priya Nair",
        "specialty": "Oncology",
        "organization": "Lotus Cancer Center",
        "city": "Chennai",
        "territory": "South Zone",
    },
    {
        "name": "Dr. Kunal Verma",
        "specialty": "Pulmonology",
        "organization": "CityCare Hospital",
        "city": "Delhi",
        "territory": "North Zone",
    },
    {
        "name": "Dr. Meera Iyer",
        "specialty": "Gynecology",
        "organization": "Sunrise Women & Child Hospital",
        "city": "Hyderabad",
        "territory": "South Zone",
    },
]


MATERIAL_SEED = [
    {"name": "Product X efficacy brochure", "material_type": "Brochure"},
    {"name": "Phase III clinical reprint", "material_type": "Clinical Reprint"},
    {"name": "Dosing guide", "material_type": "Guide"},
    {"name": "Patient support leaflet", "material_type": "Leaflet"},
    {"name": "Starter sample kit", "material_type": "Sample"},
]


def seed_reference_data(db: Session) -> None:
    if not db.query(HCP).count():
        db.add_all(HCP(**item) for item in HCP_SEED)
    if not db.query(Material).count():
        db.add_all(Material(**item) for item in MATERIAL_SEED)
    db.commit()
