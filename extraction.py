import os
import base64
import json
import httpx
from pathlib import Path

SAMPLE_DATA_PATH = Path(__file__).parent / "sample_data" / "sample_extraction.json"

EXTRACTION_SYSTEM_PROMPT = """You are a specialist document analyst for NEA Singapore's Energy Labelling Scheme (ELS) television product registration. You extract structured data from TV test report PDFs.

Given a TV test report PDF, extract ALL of the following fields and return ONLY a JSON object (no markdown, no explanation). Use null for fields that are missing or cannot be determined from the document.

The test report follows a standard template with these sections:
- Section 1: Testing Laboratory
- Section 2: Product Specification (Nameplate/Catalogue)
- Section 3: Energy consumption test (On mode)
- Section 4: Energy consumption test (Standby mode)
- Section 5: Signatures
- Appendix A: Photos
- Appendix B: Schematic Drawing
- Appendix C: Component List

Return this exact JSON structure:
{
    "report_number": "string — test report reference number from the header",
    "test_date": "string — date of test from Section 1a, in dd/mm/yy format as written",
    "lab_name": "string — name of testing laboratory from Section 1b",
    "lab_address": "string — full address of testing laboratory from Section 1c",
    "lab_country": "string — country extracted from the lab address",
    "testing_officer_name": "string — name of testing officer from Section 1d",
    "testing_officer_designation": "string — designation/title of testing officer",
    "approving_officer_name": "string — name of first approving officer from Section 1e",
    "approving_officer_designation": "string — designation of first approving officer",
    "approving_officer_name_2": "string or null — name of second approving officer if present",
    "approving_officer_designation_2": "string or null — designation of second approving officer",
    "lab_type": "string — 'Manufacturer\\'s in-house testing laboratory' or 'Third-party accredited testing laboratory', inferred from context",

    "brand": "string — brand name from Section 2a",
    "phase": "string — electrical phase from Section 2b",
    "model_number": "string — model number from Section 2c",
    "display_technology": "string — type of television from Section 2d (CRT, LCD-CCFL, LCD-Edge LED, LCD-Full LED Backlight, Plasma, OLED, etc.)",
    "display_resolution": "string — display resolution from Section 2e, normalized to WxH format (e.g. 3840x2160)",
    "tuner_count": "integer — number of tuners from Section 2f",
    "voltage_rated": "string — voltage rating from Section 2g",
    "frequency_rated": "string — frequency from Section 2h",
    "current_rated": "string — current rating from Section 2i, numeric part only",
    "screen_aspect_ratio": "string — rated screen aspect ratio from Section 2j",
    "diagonal_screen_size_inches": "number — diagonal screen size in inches from Section 2k",
    "screen_length_mm": "number — rated screen length in mm from Section 2l",
    "screen_width_mm": "number — rated screen width in mm from Section 2m",
    "screen_area_mm2": "number — rated screen area in mm² from Section 2n",
    "dimensions_with_stand": "string — overall dimensions with stand from Section 2o",
    "dimensions_without_stand": "string — overall dimensions without stand from Section 2p",
    "weight_with_stand_kg": "number — weight with stand in kg from Section 2q",
    "weight_without_stand_kg": "number — weight without stand in kg from Section 2r",
    "rated_power_on_mode_w": "number — rated power input On-mode in watts from Section 2s",
    "test_standard_rated_power": "string — test standard for rated power from Section 2t",
    "rated_standby_power_w": "number — rated standby power in watts from Section 2u",
    "year_of_manufacture": "integer — year of manufacture from Section 2v",
    "country_of_origin": "string — country of origin from Section 2w",
    "colour": "string or null — cabinet colour if explicitly stated in the report text",
    "features": "string or null — product features if explicitly listed (e.g. Smart TV, 3D, HDR)",

    "on_mode_test_standard": "string — test standard from Section 3a",
    "video_signal": "string — video signal type from Section 3b",
    "terminal": "string — terminal/connection type from Section 3c",
    "source": "string — source device from Section 3d",
    "test_voltage_v": "number — measured voltage from Section 3e",
    "test_frequency_hz": "number — measured frequency from Section 3f",
    "test_current_a": "number — measured current from Section 3g",
    "ambient_temperature_c": "number — ambient temperature from Section 3h",
    "measured_screen_length_mm": "number — measured screen length from Section 3i",
    "measured_screen_width_mm": "number — measured screen width from Section 3j",
    "measured_screen_area_mm2": "number — measured screen area from Section 3k",
    "standard_mode": "string — standard picture mode name from Section 3l",
    "luminance_standard_cd_m2": "number — luminance in standard mode from Section 3n",
    "brightest_mode": "string — brightest picture mode name from Section 3o",
    "luminance_brightest_cd_m2": "number — luminance in brightest mode from Section 3p",
    "luminance_ratio_percent": "number — luminance ratio percentage from Section 3q",
    "peak_luminance_method": "string — peak luminance measuring method from Section 3r",
    "power_saving": "string — power saving function status from Section 3s (on/off)",
    "video_aspect_ratio": "string — video aspect ratio during test from Section 3t",
    "test_display_resolution": "string — display resolution during test from Section 3u, normalized WxH",
    "sound_level_mw": "number — sound level in mW from Section 3v",
    "stabilization_duration_min": "number — stabilization duration in minutes from Section 3w",
    "dynamic_broadcast_duration_min": "number — dynamic broadcast test duration in minutes from Section 3x",
    "energy_consumption_on_mode_w": "number — energy consumption On-mode at Standard mode in watts from Section 3y",

    "standby_test_standard": "string — standby test standard from Section 4a",
    "standby_voltage_v": "number — standby test voltage from Section 4b",
    "standby_frequency_hz": "number — standby test frequency from Section 4c",
    "standby_current_a": "number — standby current from Section 4d",
    "standby_ambient_temp_c": "number — standby ambient temperature from Section 4e",
    "passive_standby_power_w": "number — passive standby power in watts from Section 4f",
    "passive_standby_procedure": "string — passive standby testing procedure from Section 4g",
    "active_standby_high_w": "string or number — active standby high power from Section 4h, or 'N/A'",
    "active_standby_low_w": "string or number — active standby low power from Section 4i, or 'N/A'",
    "active_standby_procedure": "string — active standby testing procedure from Section 4j, or 'N/A'",

    "has_testing_officer_signature": "boolean — true if a visible signature mark is present for the testing officer in Section 5",
    "has_approving_officer_signature": "boolean — true if a visible signature mark is present for the approving officer in Section 5",
    "report_issue_date": "string — date from Section 5 in YYYY/MM/DD or as written",
    "has_exterior_photos": "boolean — true if Appendix A contains exterior photos (front, back, sides)",
    "has_connector_panel_photo": "boolean — true if connector panel photo is included",
    "has_nameplate_photo": "boolean — true if nameplate photo is included",
    "has_picture_settings_photos": "boolean — true if picture settings photos for standard and brightest modes are included",
    "has_aspect_ratio_test_photo": "boolean — true if video aspect ratio test photo is included",
    "has_test_equipment_photo": "boolean — true if test equipment photo is included",
    "has_test_setup_photo": "boolean — true if testing setup/connection photo is included",
    "has_schematic_drawing": "boolean — true if Appendix B contains an actual schematic drawing (not just a header)",
    "has_component_list": "boolean — true if Appendix C contains an actual component list with specifications (not just a header)",
    "nameplate_model_match": "boolean — true if model number on nameplate photo matches Section 2c, or null if nameplate photo is not readable",
    "nameplate_power_match": "boolean — true if rated power on nameplate matches Section 2s, or null if not readable",

    "registration_fields": {
        "type_of_television": "string — normalized: CRT, OLED, LCD-CCFL, LCD-Edge LED, LCD-Full LED Backlight, Plasma",
        "brand": "string",
        "model_numbers": ["array of model number strings"],
        "definition": "string — resolution label e.g. '3840x2160 UHD', '1920x1080 Full HD'",
        "diagonal_screen_size": "integer — whole number inches",
        "screen_aspect_ratio": "string",
        "colour": "string — empty string if not found",
        "year_of_manufacture": "integer",
        "country_of_origin": "string",
        "test_report_reference_no": "string",
        "date_of_issue": "string — report issue date",
        "test_standard": "string — On-mode test standard from Section 3a",
        "screen_area_dm2": "number — screen area converted from mm² to dm² (divide by 10000), rounded to 2 decimal places",
        "power_input_on_mode_w": "number — measured On-mode energy consumption from Section 3y (NOT rated power from Section 2s)",
        "passive_standby_power_w": "number — from Section 4f",
        "active_high_standby_w": "number or null — from Section 4h, null if N/A",
        "active_low_standby_w": "number or null — from Section 4i, null if N/A",
        "lab_type": "string",
        "lab_name": "string",
        "lab_address": "string",
        "lab_country": "string",
        "lab_postal_code": "string — empty if not available"
    }
}

IMPORTANT:
- Return ONLY valid JSON, no markdown fencing, no commentary.
- Use null for truly missing values, not empty strings (except where noted).
- For boolean photo/document checks, examine the actual content — a section header alone without real content means false.
- Normalize display resolution to WxH format without spaces around 'x'.
- For screen_area_dm2 in registration_fields, convert mm² to dm² by dividing by 10000.
- For power_input_on_mode_w in registration_fields, use the MEASURED On-mode consumption (Section 3y), not the nameplate rated power (Section 2s)."""


KEY_ALIASES = {
    "test_date": "date_of_test",
    "diagonal_screen_size_inches": "diagonal_screen_size",
    "weight_with_stand_kg": "weight_with_stand",
    "weight_without_stand_kg": "weight_without_stand",
    "rated_power_on_mode_w": "rated_power_on_mode",
    "test_standard_rated_power": "rated_power_test_standard",
    "rated_standby_power_w": "rated_standby_power",
    "test_voltage_v": "on_mode_voltage",
    "test_frequency_hz": "on_mode_frequency",
    "test_current_a": "on_mode_current",
    "ambient_temperature_c": "on_mode_temperature",
    "measured_screen_length_mm": "on_mode_screen_length",
    "measured_screen_width_mm": "on_mode_screen_width",
    "measured_screen_area_mm2": "on_mode_screen_area",
    "luminance_standard_cd_m2": "luminance_standard_mode",
    "luminance_brightest_cd_m2": "luminance_brightest_mode",
    "luminance_ratio_percent": "luminance_ratio",
    "peak_luminance_method": "luminance_method",
    "power_saving": "power_saving_function",
    "test_display_resolution": "on_mode_resolution",
    "sound_level_mw": "sound_level",
    "stabilization_duration_min": "stabilization_duration",
    "dynamic_broadcast_duration_min": "broadcast_duration",
    "energy_consumption_on_mode_w": "energy_consumption_on_mode",
    "source": "source_device",
    "standby_voltage_v": "standby_voltage",
    "standby_frequency_hz": "standby_frequency",
    "standby_current_a": "standby_current",
    "standby_ambient_temp_c": "standby_temperature",
    "passive_standby_power_w": "passive_standby_power",
    "active_standby_high_w": "active_standby_high",
    "active_standby_low_w": "active_standby_low",
    "voltage_rated": "spec_voltage",
    "frequency_rated": "spec_frequency",
    "current_rated": "spec_current",
}


def _normalize_keys(data: dict) -> dict:
    """Add aliased keys so validation can find fields under its expected names."""
    result = dict(data)
    for original, alias in KEY_ALIASES.items():
        if original in result and alias not in result:
            result[alias] = result[original]

    reg = result.get("registration_fields")
    if reg:
        for key in ("active_high_standby_w", "active_low_standby_w"):
            raw_key = {"active_high_standby_w": "active_standby_high_w",
                       "active_low_standby_w": "active_standby_low_w"}.get(key)
            raw_val = result.get(raw_key, "")
            if reg.get(key) is None and raw_val:
                reg[key] = str(raw_val)

    return result


def _get_secret(key, default=None):
    """Get a secret from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


def _get_api_config():
    """Get API base URL and auth header from environment or Streamlit secrets."""
    auth_token = _get_secret("ANTHROPIC_AUTH_TOKEN")
    base_url = _get_secret("ANTHROPIC_BASE_URL")
    api_key = _get_secret("ANTHROPIC_API_KEY")

    if auth_token and base_url:
        return base_url.rstrip("/"), {"x-api-key": auth_token}
    elif api_key:
        return "https://api.anthropic.com", {"x-api-key": api_key}
    elif auth_token:
        return "https://api.anthropic.com", {"x-api-key": auth_token}
    else:
        raise ValueError(
            "No Claude credentials found. Set ANTHROPIC_API_KEY or "
            "ANTHROPIC_AUTH_TOKEN in Streamlit secrets."
        )


def _get_model():
    """Get the model ID from environment, Streamlit secrets, or use default."""
    return _get_secret("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-20250514")


def extract_from_pdf(pdf_bytes: bytes) -> dict:
    """Extract TV test report data from PDF using Claude API."""
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
        "system": EXTRACTION_SYSTEM_PROMPT,
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
                        "text": "Extract all fields from this TV test report PDF and return the structured JSON as specified.",
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
    raw_text = data["content"][0]["text"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")]
        raw_text = raw_text.strip()

    return _normalize_keys(json.loads(raw_text))


def get_demo_data() -> dict:
    """Return pre-computed extraction results for demo mode."""
    with open(SAMPLE_DATA_PATH, "r") as f:
        return _normalize_keys(json.load(f))
