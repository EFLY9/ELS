"""ELS Refrigerator Test Report Validation Engine.

Implements ~33 compliance checks against extracted refrigerator test report data,
organized by the sections of the NEA refrigerator test report template.
"""

import re


def _parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".")
    match = re.search(r'[-+]?\d+\.?\d*', s)
    if match:
        return float(match.group())
    return None


def _is_present(value):
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in ("", "N/A", "n/a", "NA", "na", "-"):
        return False
    return True


def _check(name, section, passed, extracted_value, expected, reason):
    return {
        "name": name,
        "section": section,
        "passed": passed,
        "extracted_value": str(extracted_value) if extracted_value is not None else None,
        "expected": expected,
        "reason": reason,
    }


# ── Section 1: Testing Laboratory ────────────────────────────────────────────

def _validate_section1(data):
    S = "Section 1: Testing Laboratory"
    checks = []

    val = data.get("report_number")
    checks.append(_check(
        "Report Number", S,
        _is_present(val), val,
        "Report reference number provided",
        f"Report number: {val}." if _is_present(val) else "Report number is missing.",
    ))

    val = data.get("date_of_test") or data.get("test_date")
    checks.append(_check(
        "Date of Testing", S,
        _is_present(val), val,
        "Test date provided",
        f"Test date: {val}." if _is_present(val) else "Test date is missing.",
    ))

    val = data.get("lab_name")
    checks.append(_check(
        "Testing Laboratory Name", S,
        _is_present(val), val,
        "Lab name provided",
        f"Lab: {val}." if _is_present(val) else "Laboratory name is missing.",
    ))

    val = data.get("lab_address")
    checks.append(_check(
        "Laboratory Address", S,
        _is_present(val), val,
        "Lab address provided",
        f"Address documented." if _is_present(val) else "Laboratory address is missing.",
    ))

    val = data.get("lab_country")
    checks.append(_check(
        "Laboratory Country", S,
        _is_present(val), val,
        "Lab country provided",
        f"Country: {val}." if _is_present(val) else "Laboratory country is missing.",
    ))

    name_val = data.get("testing_officer_name")
    desig_val = data.get("testing_officer_designation")
    both = _is_present(name_val) and _is_present(desig_val)
    checks.append(_check(
        "Testing Officer Details", S,
        both, f"{name_val} / {desig_val}" if both else name_val,
        "Name and designation provided",
        f"Testing officer: {name_val}, {desig_val}." if both
        else "Testing officer name or designation is missing.",
    ))

    name_val = data.get("approving_officer_name")
    desig_val = data.get("approving_officer_designation")
    both = _is_present(name_val) and _is_present(desig_val)
    checks.append(_check(
        "Approving Officer Details", S,
        both, f"{name_val} / {desig_val}" if both else name_val,
        "Name and designation provided",
        f"Approving officer: {name_val}, {desig_val}." if both
        else "Approving officer name or designation is missing.",
    ))

    return checks


# ── Section 2: Product Specification ─────────────────────────────────────────

def _validate_section2(data):
    S = "Section 2: Product Specification"
    checks = []

    val = data.get("brand")
    checks.append(_check(
        "Brand", S,
        _is_present(val), val,
        "Brand name provided",
        f"Brand: {val}." if _is_present(val) else "Brand name is missing.",
    ))

    val = data.get("refrigerator_type") or data.get("type")
    checks.append(_check(
        "Refrigerator Type", S,
        _is_present(val), val,
        "Refrigerator type documented",
        f"Type: {val}." if _is_present(val) else "Refrigerator type is missing.",
    ))

    val = data.get("model_number")
    present = _is_present(val)
    models = [m.strip() for m in re.split(r'[,;]', str(val)) if m.strip()] if present else []
    single = len(models) == 1
    checks.append(_check(
        "Model Number", S,
        present and single, val,
        "Exactly one model number",
        f"Single model: {val}." if present and single
        else "Multiple model numbers found — only one allowed." if present
        else "Model number is missing.",
    ))

    val = data.get("country_of_origin")
    checks.append(_check(
        "Country of Origin", S,
        _is_present(val), val,
        "Country of origin provided",
        f"Country: {val}." if _is_present(val) else "Country of origin is missing.",
    ))

    val = data.get("refrigerant_type")
    checks.append(_check(
        "Type of Refrigerant", S,
        _is_present(val), val,
        "Refrigerant type documented",
        f"Refrigerant: {val}." if _is_present(val) else "Type of refrigerant is missing.",
    ))

    val = data.get("total_refrigerant_charge_g") or data.get("total_refrigerant_charge_kg") or data.get("refrigerant_charge_kg") or data.get("refrigerant_charge_g")
    num = _parse_number(val)
    checks.append(_check(
        "Total Refrigerant Charge", S,
        num is not None and num > 0, val,
        "Numeric refrigerant charge",
        f"Charge: {val}." if num is not None else "Total refrigerant charge is missing or non-numeric.",
    ))

    val = data.get("weight_kg")
    checks.append(_check(
        "Weight", S,
        _is_present(val), val,
        "Weight documented",
        f"Weight: {val} kg." if _is_present(val) else "Weight is missing.",
    ))

    val = data.get("overall_dimensions") or data.get("dimensions_overall")
    checks.append(_check(
        "Overall Dimensions", S,
        _is_present(val), val,
        "Dimensions (h x w x d) documented",
        f"Dimensions: {val}." if _is_present(val) else "Overall dimensions are missing.",
    ))

    return checks


# ── Section 3: Energy Consumption Test ───────────────────────────────────────

def _validate_section3(data):
    S = "Section 3: Energy Consumption Test"
    checks = []

    val = data.get("test_standard")
    present = _is_present(val)
    is_62552 = "62552" in str(val) if present else False
    checks.append(_check(
        "Test Standard", S,
        present and is_62552, val,
        "IEC 62552 (any edition)",
        f"Test standard: {val}." if present and is_62552
        else f"Test standard present but not IEC 62552: {val}." if present
        else "Test standard is missing.",
    ))

    val = data.get("test_voltage_v")
    num = _parse_number(val)
    in_range = num is not None and 220 <= num <= 240
    checks.append(_check(
        "Test Voltage", S,
        in_range if num is not None else False, val,
        "220–240V",
        f"Voltage: {val}V." if in_range
        else f"Voltage {val} outside 220–240V range." if num is not None
        else "Test voltage is missing.",
    ))

    val = data.get("test_frequency_hz")
    num = _parse_number(val)
    is_50 = num is not None and 49 <= num <= 51
    checks.append(_check(
        "Test Frequency", S,
        is_50 if num is not None else False, val,
        "50Hz",
        f"Frequency: {val}Hz." if is_50
        else f"Frequency {val} — expected 50Hz." if num is not None
        else "Test frequency is missing.",
    ))

    val = data.get("ambient_temperature_c") or data.get("nominal_ambient_temp_c")
    num = _parse_number(val)
    in_range = num is not None and 31 <= num <= 33
    checks.append(_check(
        "Ambient Temperature", S,
        in_range if num is not None else False, val,
        "32°C (tropical, 31–33°C acceptable)",
        f"Ambient temp: {val}°C." if in_range
        else f"Ambient temp {val}°C — expected ~32°C." if num is not None
        else "Ambient temperature is missing.",
    ))

    val = data.get("total_volume_measured_l")
    num = _parse_number(val)
    checks.append(_check(
        "Total Volume (Measured)", S,
        num is not None and num > 0, val,
        "Measured total volume in litres",
        f"Measured volume: {val}L." if num is not None and num > 0
        else "Measured total volume is missing or invalid.",
    ))

    val = data.get("total_adjusted_volume_rated_l")
    num = _parse_number(val)
    within_meps = num is not None and num <= 900
    checks.append(_check(
        "Total Adjusted Volume (Rated)", S,
        num is not None and within_meps, val,
        "Numeric, ≤ 900L (MEPS threshold)",
        f"Adjusted volume: {val}L." if num is not None and within_meps
        else f"Adjusted volume {val}L exceeds 900L MEPS threshold." if num is not None
        else "Total adjusted volume (rated) is missing.",
    ))

    val = data.get("annual_energy_consumption_kwh")
    num = _parse_number(val)
    checks.append(_check(
        "Annual Energy Consumption", S,
        num is not None and num > 0, val,
        "Numeric annual energy consumption (kWh)",
        f"AEC: {val} kWh." if num is not None and num > 0
        else "Annual energy consumption is missing or invalid.",
    ))

    val = data.get("energy_efficiency_ticks")
    num = _parse_number(val)
    in_range = num is not None and 1 <= num <= 4
    checks.append(_check(
        "Energy Efficiency Ticks", S,
        in_range, val,
        "1–4 ticks",
        f"Ticks: {int(num)}." if in_range
        else f"Ticks value {val} — expected 1–4." if num is not None
        else "Energy efficiency ticks is missing.",
    ))

    cold = data.get("daily_energy_cold_wh")
    warm = data.get("daily_energy_warm_wh")
    has_daily = _is_present(cold) or _is_present(warm)
    display = f"Cold: {cold} Wh, Warm: {warm} Wh" if has_daily else None
    checks.append(_check(
        "Daily Energy Consumption", S,
        has_daily, display,
        "At least one daily energy value (cold or warm)",
        f"Daily energy documented." if has_daily
        else "Daily energy consumption values are missing.",
    ))

    interp = data.get("interpolation_valid")
    daily_interp = data.get("daily_energy_interpolated_wh")
    has_interp = _is_present(interp) or _is_present(daily_interp) or (cold is not None and warm is not None)
    checks.append(_check(
        "Interpolation Results", S,
        has_interp, interp or daily_interp,
        "Interpolation results documented",
        f"Interpolation documented." if has_interp
        else "Interpolation results are missing.",
    ))

    return checks


# ── Section 4 + Appendices ───────────────────────────────────────────────────

def _validate_section4(data):
    S = "Section 4: Signatures & Appendices"
    checks = []

    val = data.get("has_testing_officer_signature")
    checks.append(_check(
        "Testing Officer Signature", S,
        val is True, val,
        "Visible signature present",
        "Testing officer signature present." if val is True
        else "Testing officer signature not found.",
    ))

    val = data.get("has_approving_officer_signature")
    checks.append(_check(
        "Approving Officer Signature", S,
        val is True, val,
        "Visible signature present",
        "Approving officer signature present." if val is True
        else "Approving officer signature not found.",
    ))

    t_name = str(data.get("testing_officer_name", "")).strip().lower()
    a_name = str(data.get("approving_officer_name", "")).strip().lower()
    distinct = bool(t_name and a_name and t_name != a_name)
    checks.append(_check(
        "Signature Distinctness", S,
        distinct,
        f"Testing: {data.get('testing_officer_name')} | Approving: {data.get('approving_officer_name')}",
        "Two distinct individuals",
        "Officers are distinct." if distinct else "Officers appear to be the same person or names missing.",
    ))

    val = data.get("report_issue_date")
    checks.append(_check(
        "Report Date", S,
        _is_present(val), val,
        "Issue/signature date present",
        f"Date: {val}." if _is_present(val) else "Report issue date is missing.",
    ))

    for field, label, desc in [
        ("has_exterior_photos", "Exterior/Interior Photos", "Exterior and interior photos"),
        ("has_nameplate_photo", "Nameplate Photo", "Nameplate photo"),
        ("has_schematic_drawing", "Schematic Drawing", "Schematic/wiring drawing"),
        ("has_component_list", "Component List", "Component list with specs"),
    ]:
        val = data.get(field)
        passed = val is True
        checks.append(_check(
            label, S,
            passed if val is not None else None, val,
            desc,
            f"{label}: present." if passed
            else f"{label}: not found in document." if val is False
            else f"{label}: unable to verify.",
        ))

    return checks


# ── Main Entry Point ─────────────────────────────────────────────────────────

def validate_fridge(data: dict) -> dict:
    """Run all refrigerator validation checks against extracted data."""
    all_checks = []
    sections = []

    for validator, title in [
        (_validate_section1, "Section 1: Testing Laboratory"),
        (_validate_section2, "Section 2: Product Specification"),
        (_validate_section3, "Section 3: Energy Consumption Test"),
        (_validate_section4, "Section 4: Signatures & Appendices"),
    ]:
        checks = validator(data)
        all_checks.extend(checks)
        sec_passed = sum(1 for c in checks if c["passed"] is True)
        sec_failed = sum(1 for c in checks if c["passed"] is False)
        sec_warn = sum(1 for c in checks if c["passed"] is None)
        sections.append({
            "name": title,
            "checks": checks,
            "summary": {
                "total": len(checks),
                "passed": sec_passed,
                "failed": sec_failed,
                "warnings": sec_warn,
            },
        })

    total = len(all_checks)
    passed = sum(1 for c in all_checks if c["passed"] is True)
    failed = sum(1 for c in all_checks if c["passed"] is False)
    warnings = sum(1 for c in all_checks if c["passed"] is None)

    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
        },
        "sections": sections,
    }
