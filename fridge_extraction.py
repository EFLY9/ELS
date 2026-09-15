import base64
import json
import httpx
from pathlib import Path

from extraction import _get_api_config, _get_model

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sample_fridge_extraction.json"

FRIDGE_EXTRACTION_PROMPT = """You are a specialist document analyst for NEA Singapore's Energy Labelling Scheme (ELS) refrigerator product registration. You extract structured data from refrigerator test report PDFs.

Given a refrigerator test report PDF, extract ALL of the following fields and return ONLY a JSON object (no markdown, no explanation). Use null for fields that are missing or cannot be determined from the document.

The test report follows a standard template with these sections:
- Section 1: Testing Laboratory
- Section 2: Product Specification
- Section 3: Energy consumption test (IEC 62552)
- Section 4: Signatures
- Appendix A: Photos (exterior, interior, compressor, nameplate, temperature settings)
- Appendix B: Schematic Drawing
- Appendix C: Component List
- Appendix D: Temperature sensors layout plan

Return this exact JSON structure:
{
    "report_number": "string — test report reference number from the header, e.g. THES260400027201",
    "test_date": "string — date of test from Section 1a, as written (may be a range like 2026/05/08~2026/06/17)",
    "lab_name": "string — name of testing laboratory from Section 1b",
    "lab_address": "string — full address of testing laboratory from Section 1c",
    "lab_country": "string — country extracted from the lab address",
    "testing_officer_name": "string — name of testing officer from Section 1d",
    "testing_officer_designation": "string — designation/title of testing officer",
    "approving_officer_name": "string — name of approving officer from Section 1e",
    "approving_officer_designation": "string — designation of approving officer",
    "lab_type": "string — 'Manufacturer\\'s in-house testing laboratory' or 'Third-party accredited testing laboratory', inferred from lab name and context",

    "brand": "string — brand name from Section 2a",
    "type": "string — type of refrigerator from Section 2b (e.g. 'Refrigerator with freezer', 'Refrigerator without freezer')",
    "phase": "string — electrical phase from Section 2c",
    "country_of_origin": "string — country of origin from Section 2d",
    "refrigerant_type": "string — type of refrigerant from Section 2e (e.g. R600a, R134a)",
    "refrigerant_charge_kg": "number or string — total refrigerant charge in kg from Section 2f, as written",
    "model_number": "string — model number from Section 2g",
    "voltage_rated": "string — voltage rating from Section 2h",
    "frequency_rated": "string — frequency from Section 2i",
    "current_rated": "string — current rating from Section 2j",
    "weight_kg": "number or string — weight in kg from Section 2k",
    "freezer_stars": "integer — type of freezer 1-4 stars from Section 2l",
    "dimensions_overall": "string — overall dimensions h x w x d in mm from Section 2m",
    "dimensions_in_use": "string — overall space required in use h x w x d in mm from Section 2n",

    "test_standard": "string — test standard from Section 3a (e.g. IEC 62552-1:2015/A1:2020)",
    "total_volume_rated_l": "number — rated total volume in litres from Section 3b",
    "total_volume_measured_l": "number — measured total volume in litres from Section 3b",
    "freezer_volume_rated_l": "number — rated freezer compartment volume in litres",
    "freezer_volume_measured_l": "number — measured freezer compartment volume in litres",
    "fresh_food_volume_rated_l": "number — rated fresh food compartment volume in litres",
    "fresh_food_volume_measured_l": "number — measured fresh food compartment volume in litres",
    "total_adjusted_volume_rated_l": "number — rated total adjusted volume in litres from Section 3d",
    "total_adjusted_volume_measured_l": "number — measured total adjusted volume in litres from Section 3d",
    "test_voltage_v": "number — measured voltage during test from Section 3e",
    "test_frequency_hz": "number — measured frequency during test from Section 3f",
    "test_humidity_percent": "number — humidity during test from Section 3h",
    "nominal_ambient_temp_c": "number — nominal ambient temperature from Section 3i(ii), typically 32",
    "annual_energy_consumption_kwh": "number — annual energy consumption from Section 3n (the calculated AEC value)",
    "energy_efficiency_ticks": "integer — energy efficiency class in ticks (1-4) from the calculation section",
    "daily_energy_cold_wh": "number — daily energy consumption Edaily for cold setting from Section 3j(i)",
    "daily_energy_warm_wh": "number — daily energy consumption Edaily for warm setting from Section 3j(i)",

    "has_testing_officer_signature": "boolean — true if a visible signature mark is present for the testing officer in Section 4",
    "has_approving_officer_signature": "boolean — true if a visible signature mark is present for the approving officer in Section 4",
    "report_issue_date": "string — date from Section 4",
    "has_exterior_photos": "boolean — true if Appendix A contains exterior photos (front, rear views)",
    "has_interior_photos": "boolean — true if Appendix A contains interior/open view photos",
    "has_compressor_photo": "boolean — true if compressor photo is included",
    "has_nameplate_photo": "boolean — true if nameplate photo is included",
    "has_temperature_settings_photos": "boolean — true if temperature control settings photos are included",
    "has_schematic_drawing": "boolean — true if Appendix B contains an actual schematic/wiring drawing (not just a header)",
    "has_component_list": "boolean — true if Appendix C contains an actual component list with specifications (not just a header)",
    "has_sensor_layout": "boolean — true if Appendix D contains temperature sensor layout diagrams",

    "registration_fields": {
        "type": "string — refrigerator type (e.g. 'Refrigerator with freezer')",
        "brand": "string",
        "model_numbers": ["array of model number strings — primary tested model first"],
        "colour": "string — colour if determinable from nameplate, model suffix, or photos; empty string if not",
        "features": "string — features if listed; empty string if not explicitly stated",
        "country_of_origin": "string",
        "refrigerant_type": "string — e.g. R600a",
        "refrigerant_charge_g": "integer — total refrigerant charge converted to grams (multiply kg by 1000)",
        "test_report_reference_no": "string — the report reference number",
        "date_of_issue": "string — report issue date from Section 4",
        "test_standard": "string — test standard from Section 3a",
        "total_volume_measured_l": "integer — measured total volume rounded to nearest integer",
        "total_adjusted_volume_rated_l": "integer — rated total adjusted volume rounded to nearest integer",
        "annual_energy_consumption_kwh": "integer — annual energy consumption rounded to nearest integer",
        "lab_type": "string",
        "lab_name": "string",
        "lab_address": "string",
        "lab_country": "string"
    }
}

IMPORTANT:
- Return ONLY valid JSON, no markdown fencing, no commentary.
- Use null for truly missing values, not empty strings (except where noted).
- For boolean photo/document checks, examine the actual content — a section header alone without real content means false.
- For refrigerant_charge_g in registration_fields, convert from kg to grams (multiply by 1000).
- For volume and energy values in registration_fields, round to nearest integer.
- The annual_energy_consumption_kwh should be the final calculated AEC value from Section 3n."""


def extract_fridge_from_pdf(pdf_bytes: bytes) -> dict:
    """Extract refrigerator test report data from PDF using Claude API."""
    base_url, headers = _get_api_config()
    model = _get_model()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    headers.update({
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    })

    payload = {
        "model": model,
        "max_tokens": 8192,
        "system": FRIDGE_EXTRACTION_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract all fields from this refrigerator test report PDF and return the structured JSON as specified.",
                    },
                ],
            }
        ],
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{base_url}/v1/messages", headers=headers, json=payload)

    if resp.status_code != 200:
        raise ValueError(f"API error ({resp.status_code}): {resp.text[:500]}")

    data = resp.json()
    raw_text = next((b["text"] for b in data["content"] if b["type"] == "text"), "")
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")]
        raw_text = raw_text.strip()

    return json.loads(raw_text)


def get_fridge_demo_data() -> dict:
    """Return pre-computed extraction results for refrigerator demo mode."""
    with open(SAMPLE_DATA_PATH, "r") as f:
        return json.load(f)
