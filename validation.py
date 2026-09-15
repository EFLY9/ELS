"""ELS TV Test Report Validation Engine.

Implements 60+ compliance checks against extracted TV test report data,
organized by the 5 sections of the NEA test report template.
"""

import re
import math
from datetime import datetime


def _parse_number(value):
    """Extract a numeric value from a string that may contain units."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    match = re.search(r'[-+]?\d+\.?\d*', s)
    if match:
        return float(match.group())
    return None


def _is_present(value):
    """Check if a value is present and non-empty."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in ("", "N/A", "n/a", "NA", "na", "-"):
        return False
    return True


def _is_na(value):
    """Check if a value is explicitly N/A."""
    if value is None:
        return False
    s = str(value).strip().upper()
    return s in ("N/A", "NA", "NOT APPLICABLE", "-")


def _check(name, section, passed, extracted_value, expected, reason):
    return {
        "name": name,
        "section": section,
        "passed": passed,
        "extracted_value": str(extracted_value) if extracted_value is not None else None,
        "expected": expected,
        "reason": reason,
    }


# ── Section 1: Testing Laboratory ──────────────────────────────────────────

def _validate_section1(data):
    S = "Section 1: Testing Laboratory"
    checks = []

    # 1. Report Number
    val = data.get("report_number")
    checks.append(_check(
        "Report Number", S,
        _is_present(val), val,
        "A clear report reference number",
        "Report number is present." if _is_present(val) else "Report reference number is missing.",
    ))

    # 2. Date of Testing
    val = data.get("date_of_test")
    checks.append(_check(
        "Date of Testing", S,
        _is_present(val), val,
        "Test date provided",
        "Test date is documented." if _is_present(val) else "Test date is missing.",
    ))

    # 3. Testing Laboratory Name
    val = data.get("lab_name")
    checks.append(_check(
        "Testing Laboratory Name", S,
        _is_present(val), val,
        "Lab name provided",
        "Laboratory name is provided." if _is_present(val) else "Laboratory name is missing.",
    ))

    # 4. Laboratory Physical Address
    val = data.get("lab_address")
    checks.append(_check(
        "Laboratory Physical Address", S,
        _is_present(val), val,
        "An address is provided",
        "Laboratory address is documented." if _is_present(val) else "Laboratory address is missing.",
    ))

    # 5. Country of Laboratory
    val = data.get("lab_country")
    checks.append(_check(
        "Country of Laboratory", S,
        _is_present(val), val,
        "Country provided",
        "Laboratory country is documented." if _is_present(val) else "Laboratory country is missing.",
    ))

    # 6. Testing Officer Details
    name_val = data.get("testing_officer_name")
    desig_val = data.get("testing_officer_designation")
    both = _is_present(name_val) and _is_present(desig_val)
    combined = f"{name_val or ''} / {desig_val or ''}"
    checks.append(_check(
        "Testing Officer Details", S,
        both, combined,
        "Full name and professional designation",
        "Testing officer name and designation are documented." if both
        else "Testing officer details incomplete — need both name and designation.",
    ))

    # 7. Approving Officer Details
    name_val = data.get("approving_officer_name")
    desig_val = data.get("approving_officer_designation")
    both = _is_present(name_val) and _is_present(desig_val)
    combined = f"{name_val or ''} / {desig_val or ''}"
    checks.append(_check(
        "Approving Officer Details", S,
        both, combined,
        "Full name and professional designation",
        "Approving officer name and designation are documented." if both
        else "Approving officer details incomplete — need both name and designation.",
    ))

    # 8. Segregation of Duties
    t_name = str(data.get("testing_officer_name", "")).strip().lower()
    a_name = str(data.get("approving_officer_name", "")).strip().lower()
    distinct = bool(t_name and a_name and t_name != a_name)
    checks.append(_check(
        "Segregation of Duties", S,
        distinct,
        f"Testing: {data.get('testing_officer_name')} | Approving: {data.get('approving_officer_name')}",
        "Two distinct individuals",
        "Testing and approving officers are different individuals." if distinct
        else "Testing and approving officers appear to be the same person or are missing.",
    ))

    # 9. Laboratory Qualification
    val = data.get("lab_type")
    present = _is_present(val)
    lab_class = None
    if present:
        v = str(val).lower()
        if "in-house" in v or "manufacturer" in v:
            lab_class = "Manufacturer's in-house testing laboratory"
        else:
            lab_class = "Third-party accredited testing laboratory"
    checks.append(_check(
        "Laboratory Qualification", S,
        present, lab_class or val,
        "Laboratory type documented",
        f"Laboratory classified as: {lab_class}." if lab_class
        else "Laboratory type/qualification is not documented.",
    ))

    return checks


# ── Section 2: Product Specification ───────────────────────────────────────

def _validate_section2(data):
    S = "Section 2: Product Specification"
    checks = []

    # 1. Brand Name
    val = data.get("brand")
    checks.append(_check(
        "Brand Name", S,
        _is_present(val), val,
        "Brand name provided",
        "Brand name is provided." if _is_present(val) else "Brand name is missing.",
    ))

    # 2. Product Model Number
    val = data.get("model_number")
    present = _is_present(val)
    models = [m.strip() for m in re.split(r'[,;]', str(val)) if m.strip()] if present else []
    single = len(models) == 1
    checks.append(_check(
        "Product Model Number", S,
        present and single, val,
        "Exactly one model number",
        f"Single model number documented: {val}." if present and single
        else "Multiple model numbers found — only one allowed." if present
        else "Model number is missing.",
    ))

    # 4. Display Technology
    val = data.get("display_technology")
    present = _is_present(val)
    normalized = None
    if present:
        v = str(val).upper().strip()
        if "OLED" in v:
            normalized = "OLED"
        elif "CRT" in v:
            normalized = "CRT"
        elif "LCD" in v or "LED" in v:
            normalized = "LCD-LED"
        else:
            normalized = v
    valid_types = {"CRT", "OLED", "LCD-LED"}
    passed = normalized in valid_types if normalized else False
    checks.append(_check(
        "Display Technology", S,
        passed, f"{val} → {normalized}" if normalized else val,
        "CRT, OLED, or LCD-LED",
        f"Display type: {normalized}." if passed
        else f"Display technology '{val}' not recognized as CRT/OLED/LCD-LED." if present
        else "Display technology is missing.",
    ))

    # 5. Display Resolution
    val = data.get("display_resolution")
    present = _is_present(val)
    standard_resolutions = {"1280x720", "1920x1080", "3840x2160", "7680x4320"}
    normalized_res = None
    if present:
        cleaned = re.sub(r'[^0-9x×X]', '', str(val)).lower().replace('×', 'x')
        for sr in standard_resolutions:
            if sr in cleaned:
                normalized_res = sr
                break
        if not normalized_res:
            nums = re.findall(r'\d+', str(val))
            if len(nums) >= 2:
                normalized_res = f"{nums[0]}x{nums[1]}"
    checks.append(_check(
        "Display Resolution", S,
        present, f"{val} → {normalized_res}" if normalized_res else val,
        "Standard resolution documented",
        f"Resolution: {normalized_res}." if present
        else "Display resolution is missing.",
    ))

    # 6. Tuner
    val = data.get("tuner_count")
    num = _parse_number(val)
    passed = num is not None and num >= 1
    checks.append(_check(
        "Tuner", S,
        passed, val,
        "At least 1 tuner",
        f"Tuner count: {int(num)}." if passed
        else "No tuner documented or count is 0.",
    ))

    # 7–9. Voltage, Frequency, Current
    for field, label, unit in [
        ("spec_voltage", "Voltage (V)", "V"),
        ("spec_frequency", "Frequency (Hz)", "Hz"),
    ]:
        val = data.get(field)
        checks.append(_check(
            label, S,
            _is_present(val), val,
            f"{label} provided",
            f"{label}: {val}." if _is_present(val) else f"{label} is missing.",
        ))

    # 10. Screen Aspect Ratio
    val = data.get("screen_aspect_ratio")
    checks.append(_check(
        "Screen Aspect Ratio", S,
        _is_present(val), val,
        "Aspect ratio documented (e.g. 16:9)",
        f"Screen aspect ratio: {val}." if _is_present(val) else "Screen aspect ratio is missing.",
    ))

    # 11. Diagonal Screen Size
    val = data.get("diagonal_screen_size")
    checks.append(_check(
        "Diagonal Screen Size", S,
        _is_present(val), val,
        "Diagonal size in inches",
        f"Diagonal screen size: {val} inches." if _is_present(val) else "Diagonal screen size is missing.",
    ))

    # 12. Viewable Screen Length
    val = data.get("screen_length_mm")
    checks.append(_check(
        "Viewable Screen Length", S,
        _is_present(val), val,
        "Screen length in mm",
        f"Screen length: {val} mm." if _is_present(val) else "Screen length is missing.",
    ))

    # 13. Viewable Screen Width
    val = data.get("screen_width_mm")
    checks.append(_check(
        "Viewable Screen Width", S,
        _is_present(val), val,
        "Screen width in mm",
        f"Screen width: {val} mm." if _is_present(val) else "Screen width is missing.",
    ))

    # 14. Screen Area Verification
    length = _parse_number(data.get("screen_length_mm"))
    width = _parse_number(data.get("screen_width_mm"))
    documented_area = _parse_number(data.get("screen_area_mm2"))
    calculated_area = length * width if length and width else None
    if calculated_area is not None and documented_area is not None:
        tolerance = max(abs(documented_area) * 0.01, 1)
        match = abs(calculated_area - documented_area) <= tolerance
    else:
        match = None
    checks.append(_check(
        "Screen Area Verification", S,
        match,
        f"Documented: {documented_area}, Calculated: {calculated_area}",
        "Calculated L×W matches documented area",
        f"Screen area verified: {calculated_area:.2f} mm² ≈ documented {documented_area} mm²." if match is True
        else f"Screen area mismatch: calculated {calculated_area:.2f} mm² vs documented {documented_area} mm²." if match is False
        else "Cannot verify screen area — length, width, or area missing.",
    ))

    # 15–18. Dimensions and weights
    for field, label in [
        ("dimensions_with_stand", "Dimensions (With Stand)"),
        ("dimensions_without_stand", "Dimensions (Without Stand)"),
        ("weight_with_stand", "Weight (With Stand)"),
        ("weight_without_stand", "Weight (Without Stand)"),
    ]:
        val = data.get(field)
        checks.append(_check(
            label, S,
            _is_present(val), val,
            f"{label} documented",
            f"{label}: {val}." if _is_present(val) else f"{label} is missing.",
        ))

    return checks


# ── Section 3: Energy Consumption On-Mode ──────────────────────────────────

def _validate_section3(data):
    S = "Section 3: Energy Consumption (On Mode)"
    checks = []

    # 1. Rated On-Mode Power
    val = data.get("rated_power_on_mode")
    checks.append(_check(
        "Rated On-Mode Power", S,
        _is_present(val), val,
        "Rated power input documented",
        f"Rated on-mode power: {val}." if _is_present(val) else "Rated on-mode power is missing.",
    ))

    # 2. Test Standard Citation (Section 2t)
    val = data.get("rated_power_test_standard")
    checks.append(_check(
        "Test Standard Citation", S,
        _is_present(val), val,
        "Test standard reference provided",
        f"Test standard for rated power: {val}." if _is_present(val) else "Test standard citation is missing.",
    ))

    # 3. Rated Standby Power
    val = data.get("rated_standby_power")
    checks.append(_check(
        "Rated Standby Power", S,
        _is_present(val), val,
        "Rated standby power documented",
        f"Rated standby power: {val}." if _is_present(val) else "Rated standby power is missing.",
    ))

    # 4. Year of Manufacture
    val = data.get("year_of_manufacture")
    checks.append(_check(
        "Year of Manufacture", S,
        _is_present(val), val,
        "Year provided",
        f"Year of manufacture: {val}." if _is_present(val) else "Year of manufacture is missing.",
    ))

    # 5. Country of Origin
    val = data.get("country_of_origin")
    checks.append(_check(
        "Country of Origin", S,
        _is_present(val), val,
        "At least one country",
        f"Country of origin: {val}." if _is_present(val) else "Country of origin is missing.",
    ))

    # 6. Cabinet Color
    val = data.get("colour")
    checks.append(_check(
        "Cabinet Color", S,
        _is_present(val), val,
        "Colour provided",
        f"Colour: {val}." if _is_present(val) else "Cabinet colour is missing.",
    ))

    # 7. Product Features
    val = data.get("features")
    checks.append(_check(
        "Product Features", S,
        _is_present(val), val,
        "Features provided",
        f"Features: {val}." if _is_present(val) else "Product features are missing.",
    ))

    # 8. Active Test Standard
    val = data.get("on_mode_test_standard")
    present = _is_present(val)
    accepted = False
    if present:
        v = str(val).upper().replace(" ", "")
        accepted = any(std in v for std in ["62087-3:2015", "62087:2011", "62087:2015", "62087"])
    checks.append(_check(
        "Active Test Standard", S,
        accepted, val,
        "IEC 62087-3:2015 (or IEC 62087:2011)",
        f"Test standard: {val}." if accepted
        else f"Test standard '{val}' does not match IEC 62087." if present
        else "On-mode test standard is missing.",
    ))

    # 9. Video Test Signal
    val = data.get("video_signal")
    present = _is_present(val)
    passed = "dynamic" in str(val).lower() and "broadcast" in str(val).lower() if present else False
    checks.append(_check(
        "Video Test Signal", S,
        passed, val,
        "Dynamic broadcast signal",
        f"Video signal: {val}." if passed
        else f"Video signal '{val}' is not 'dynamic broadcast'." if present
        else "Video signal type is missing.",
    ))

    # 10. Input Connection Port
    val = data.get("terminal")
    checks.append(_check(
        "Input Connection Port", S,
        _is_present(val), val,
        "HDMI or alternative specified",
        f"Terminal: {val}." if _is_present(val) else "Input terminal is missing.",
    ))

    # 11. Signal Source Hardware
    val = data.get("source_device")
    present = _is_present(val)
    passed = any(kw in str(val).lower() for kw in ["dvd", "blu-ray", "blu ray", "bluray"]) if present else False
    checks.append(_check(
        "Signal Source Hardware", S,
        passed, val,
        "Blu-Ray or DVD",
        f"Source device: {val}." if passed
        else f"Source device '{val}' is not Blu-Ray or DVD." if present
        else "Signal source hardware is missing.",
    ))

    # 12. Test Supply Voltage (230V ±2%)
    val = data.get("on_mode_voltage")
    num = _parse_number(val)
    passed = 225.4 <= num <= 234.6 if num is not None else False
    checks.append(_check(
        "Test Supply Voltage", S,
        passed, val,
        "230V ±2% (225.4–234.6V)",
        f"Test voltage: {num}V — within range." if passed
        else f"Test voltage: {num}V — outside 225.4–234.6V range." if num is not None
        else "Test supply voltage is missing.",
    ))

    # 13. Test Supply Frequency (50Hz ±2%)
    val = data.get("on_mode_frequency")
    num = _parse_number(val)
    passed = 49.0 <= num <= 51.0 if num is not None else False
    checks.append(_check(
        "Test Supply Frequency", S,
        passed, val,
        "50Hz ±2% (49.0–51.0Hz)",
        f"Test frequency: {num}Hz — within range." if passed
        else f"Test frequency: {num}Hz — outside 49.0–51.0Hz range." if num is not None
        else "Test supply frequency is missing.",
    ))

    # 14. Test Operating Current
    val = data.get("on_mode_current")
    checks.append(_check(
        "Test Operating Current", S,
        _is_present(val), val,
        "Operating current measured",
        f"Operating current: {val}." if _is_present(val) else "Operating current is missing.",
    ))

    # 15. Laboratory Temperature (23°C ±5°C)
    val = data.get("on_mode_temperature")
    num = _parse_number(val)
    passed = 18.0 <= num <= 28.0 if num is not None else False
    checks.append(_check(
        "Laboratory Temperature", S,
        passed, val,
        "23°C ±5°C (18–28°C)",
        f"Ambient temperature: {num}°C — within range." if passed
        else f"Ambient temperature: {num}°C — outside 18–28°C range." if num is not None
        else "Laboratory temperature is missing.",
    ))

    # 16. Measured Area Audit
    length = _parse_number(data.get("on_mode_screen_length"))
    width = _parse_number(data.get("on_mode_screen_width"))
    area = _parse_number(data.get("on_mode_screen_area"))
    if length and width and area:
        calc = length * width
        tolerance = max(abs(area) * 0.01, 1)
        passed = abs(calc - area) <= tolerance
    else:
        calc = None
        passed = None
    checks.append(_check(
        "Measured Area Audit", S,
        passed,
        f"L={length}, W={width}, Area={area}, Calc={calc}",
        "Measured area = L × W",
        f"Measured screen area matches: {calc:.2f} ≈ {area}." if passed is True
        else f"Measured area mismatch: L×W={calc:.2f} vs reported {area}." if passed is False
        else "Cannot verify — screen dimensions or area missing.",
    ))

    # 17. Standard Mode Name
    val = data.get("standard_mode")
    checks.append(_check(
        "Standard Mode Name", S,
        _is_present(val), val,
        "Standard mode specified",
        f"Standard mode: {val}." if _is_present(val) else "Standard mode name is missing.",
    ))

    # 18. Luminance Thresholds
    std_lum = _parse_number(data.get("luminance_standard_mode"))
    brightest_lum = _parse_number(data.get("luminance_brightest_mode"))
    ratio = _parse_number(data.get("luminance_ratio"))
    if brightest_lum is not None and std_lum is not None:
        if brightest_lum >= 350:
            passed = std_lum >= 228
            reason = (f"Brightest luminance ({brightest_lum} cd/m²) ≥ 350, "
                      f"standard mode ({std_lum} cd/m²) {'≥' if passed else '<'} 228 cd/m².")
        else:
            passed = ratio is not None and ratio >= 65
            reason = (f"Brightest luminance ({brightest_lum} cd/m²) < 350, "
                      f"luminance ratio ({ratio}%) {'≥' if passed else '<'} 65%.")
    else:
        passed = None
        reason = "Cannot verify luminance — values missing."
    checks.append(_check(
        "Luminance Thresholds", S,
        passed,
        f"Std: {std_lum}, Brightest: {brightest_lum}, Ratio: {ratio}%",
        "≥228 cd/m² if brightest≥350; otherwise ratio≥65%",
        reason,
    ))

    # 19. Luminance Ratio Check
    if std_lum is not None and brightest_lum is not None and brightest_lum > 0:
        calc_ratio = round((std_lum / brightest_lum) * 100, 1)
        reported = _parse_number(data.get("luminance_ratio"))
        if reported is not None:
            passed = abs(calc_ratio - reported) <= 0.5
        else:
            passed = None
    else:
        calc_ratio = None
        reported = None
        passed = None
    checks.append(_check(
        "Luminance Ratio Check", S,
        passed,
        f"Calculated: {calc_ratio}%, Reported: {reported}%",
        "Calculated ratio matches reported ratio",
        f"Luminance ratio verified: {calc_ratio}% ≈ reported {reported}%." if passed is True
        else f"Luminance ratio mismatch: calculated {calc_ratio}% vs reported {reported}%." if passed is False
        else "Cannot verify luminance ratio — values missing.",
    ))

    # 20. Brightest Mode Name
    val = data.get("brightest_mode")
    checks.append(_check(
        "Brightest Mode Name", S,
        _is_present(val), val,
        "Brightest mode specified",
        f"Brightest mode: {val}." if _is_present(val) else "Brightest mode name is missing.",
    ))

    # 21. Luminance Measurement Method
    val = data.get("luminance_method")
    checks.append(_check(
        "Luminance Measurement Method", S,
        _is_present(val), val,
        "Method documented",
        f"Luminance measurement method: {val}." if _is_present(val)
        else "Luminance measurement method is missing.",
    ))

    # 22. Power-Saving Functions
    val = data.get("power_saving_function")
    present = _is_present(val)
    passed = str(val).strip().lower() == "off" if present else False
    checks.append(_check(
        "Power-Saving Functions", S,
        passed, val,
        "Confirmed OFF",
        "Power-saving function is OFF." if passed
        else f"Power-saving function is '{val}' — must be OFF." if present
        else "Power-saving function status is missing.",
    ))

    # 23. Screen Aspect Ratio Fill
    video_ar = data.get("video_aspect_ratio")
    rated_ar = data.get("screen_aspect_ratio")
    if _is_present(video_ar) and _is_present(rated_ar):
        passed = str(video_ar).strip() == str(rated_ar).strip()
    else:
        passed = None
    checks.append(_check(
        "Screen Aspect Ratio Fill", S,
        passed,
        f"Video: {video_ar}, Rated: {rated_ar}",
        "Video aspect ratio matches rated",
        f"Video aspect ratio {video_ar} matches rated {rated_ar}." if passed is True
        else f"Video aspect ratio {video_ar} does not match rated {rated_ar}." if passed is False
        else "Cannot verify — aspect ratio values missing.",
    ))

    # 24. Resolution Consistency
    on_res = data.get("on_mode_resolution")
    spec_res = data.get("display_resolution")
    if _is_present(on_res) and _is_present(spec_res):
        clean_on = re.sub(r'[^0-9x]', '', str(on_res).lower().replace('×', 'x'))
        clean_spec = re.sub(r'[^0-9x]', '', str(spec_res).lower().replace('×', 'x'))
        passed = clean_on == clean_spec
    else:
        passed = None
    checks.append(_check(
        "Resolution Consistency", S,
        passed,
        f"On-mode: {on_res}, Spec: {spec_res}",
        "Matches Section 2 specification",
        f"Resolution consistent: {on_res} matches {spec_res}." if passed is True
        else f"Resolution mismatch: on-mode {on_res} vs spec {spec_res}." if passed is False
        else "Cannot verify resolution consistency — values missing.",
    ))

    # 25. Audio Sound Level (≥50 mW)
    val = data.get("sound_level")
    num = _parse_number(val)
    passed = num is not None and num >= 50
    checks.append(_check(
        "Audio Sound Level", S,
        passed, val,
        "At least 50 mW",
        f"Sound level: {num} mW — meets minimum." if passed
        else f"Sound level: {num} mW — below 50 mW minimum." if num is not None
        else "Sound level is missing.",
    ))

    # 26. Unit Warm-Up Duration (≥60 min)
    val = data.get("stabilization_duration")
    num = _parse_number(val)
    passed = num is not None and num >= 60
    checks.append(_check(
        "Unit Warm-Up Duration", S,
        passed, val,
        "At least 60 minutes",
        f"Stabilization duration: {num} min — meets minimum." if passed
        else f"Stabilization duration: {num} min — below 60 min minimum." if num is not None
        else "Stabilization duration is missing.",
    ))

    # 27. Test Video Run Time (10 min)
    val = data.get("broadcast_duration")
    num = _parse_number(val)
    passed = num is not None and num == 10
    checks.append(_check(
        "Test Video Run Time", S,
        passed, val,
        "10 minutes",
        f"Broadcast test duration: {num} min." if passed
        else f"Broadcast test duration: {num} min — should be 10 min." if num is not None
        else "Broadcast test duration is missing.",
    ))

    # 28. Final Energy Result
    val = data.get("energy_consumption_on_mode")
    checks.append(_check(
        "Final Energy Result", S,
        _is_present(val), val,
        "Energy consumption recorded",
        f"On-mode energy consumption: {val} W." if _is_present(val)
        else "Final on-mode energy consumption is missing.",
    ))

    return checks


# ── Section 4: Standby Mode ────────────────────────────────────────────────

def _validate_section4(data):
    S = "Section 4: Standby Mode"
    checks = []

    # 1. Standby Test Standard
    val = data.get("standby_test_standard")
    present = _is_present(val)
    accepted = "62301" in str(val).replace(" ", "") if present else False
    checks.append(_check(
        "Standby Test Standard", S,
        accepted, val,
        "IEC 62301:2011",
        f"Standby test standard: {val}." if accepted
        else f"Standby test standard '{val}' does not match IEC 62301." if present
        else "Standby test standard is missing.",
    ))

    # 2. Standby Voltage Precision (230V ±1%)
    val = data.get("standby_voltage")
    num = _parse_number(val)
    passed = 227.7 <= num <= 232.3 if num is not None else False
    checks.append(_check(
        "Standby Voltage Precision", S,
        passed, val,
        "230V ±1% (227.7–232.3V)",
        f"Standby voltage: {num}V — within range." if passed
        else f"Standby voltage: {num}V — outside 227.7–232.3V range." if num is not None
        else "Standby voltage is missing.",
    ))

    # 3. Standby Frequency Precision (50Hz ±1%)
    val = data.get("standby_frequency")
    num = _parse_number(val)
    passed = 49.5 <= num <= 50.5 if num is not None else False
    checks.append(_check(
        "Standby Frequency Precision", S,
        passed, val,
        "50Hz ±1% (49.5–50.5Hz)",
        f"Standby frequency: {num}Hz — within range." if passed
        else f"Standby frequency: {num}Hz — outside 49.5–50.5Hz range." if num is not None
        else "Standby frequency is missing.",
    ))

    # 4. Standby Current Drawn
    val = data.get("standby_current")
    checks.append(_check(
        "Standby Current Drawn", S,
        _is_present(val), val,
        "Standby current measured",
        f"Standby current: {val}." if _is_present(val) else "Standby current is missing.",
    ))

    # 5. Standby Room Temperature (23°C ±5°C)
    val = data.get("standby_temperature")
    num = _parse_number(val)
    passed = 18.0 <= num <= 28.0 if num is not None else False
    checks.append(_check(
        "Standby Room Temperature", S,
        passed, val,
        "23°C ±5°C (18–28°C)",
        f"Standby temperature: {num}°C — within range." if passed
        else f"Standby temperature: {num}°C — outside 18–28°C range." if num is not None
        else "Standby temperature is missing.",
    ))

    # 6. Passive Standby Consumption (≤0.5W)
    val = data.get("passive_standby_power")
    num = _parse_number(val)
    passed = num is not None and num <= 0.5
    checks.append(_check(
        "Passive Standby Consumption", S,
        passed, val,
        "≤ 0.5W",
        f"Passive standby power: {num}W — within limit." if passed
        else f"Passive standby power: {num}W — exceeds 0.5W limit." if num is not None
        else "Passive standby power is missing.",
    ))

    # 7. Standby Method Citation
    val = data.get("passive_standby_procedure")
    checks.append(_check(
        "Standby Method Citation", S,
        _is_present(val), val,
        "Testing procedure reference provided",
        f"Standby procedure: {val}." if _is_present(val) else "Standby testing procedure is missing.",
    ))

    # 8. Active Standby High
    val = data.get("active_standby_high")
    present = _is_present(val) or _is_na(val)
    checks.append(_check(
        "Active Standby (High Power)", S,
        present, val,
        "Measured value or N/A",
        f"Active standby high: {val}." if present
        else "Active standby high power is missing (provide value or state N/A).",
    ))

    # 9. Active Standby Low
    val = data.get("active_standby_low")
    present = _is_present(val) or _is_na(val)
    checks.append(_check(
        "Active Standby (Low Power)", S,
        present, val,
        "Measured value or N/A",
        f"Active standby low: {val}." if present
        else "Active standby low power is missing (provide value or state N/A).",
    ))

    return checks


# ── Section 5 + Appendices ─────────────────────────────────────────────────

def _validate_section5(data):
    S = "Section 5: Signatures & Appendices"
    checks = []

    # 1. Testing Officer Signature
    val = data.get("has_testing_officer_signature")
    checks.append(_check(
        "Testing Officer Signature", S,
        val is True, val,
        "Visible signature present",
        "Testing officer signature is present." if val is True
        else "Testing officer signature is missing or not visible.",
    ))

    # 2. Approving Officer Signature
    val = data.get("has_approving_officer_signature")
    checks.append(_check(
        "Approving Officer Signature", S,
        val is True, val,
        "Visible signature present",
        "Approving officer signature is present." if val is True
        else "Approving officer signature is missing or not visible.",
    ))

    # 3. Signature Distinctness
    t_name = str(data.get("testing_officer_name", "")).strip().lower()
    a_name = str(data.get("approving_officer_name", "")).strip().lower()
    distinct = bool(t_name and a_name and t_name != a_name)
    checks.append(_check(
        "Signature Distinctness", S,
        distinct,
        f"Testing: {data.get('testing_officer_name')} | Approving: {data.get('approving_officer_name')}",
        "Two distinct individuals signed",
        "Signatures are from two distinct officers." if distinct
        else "Officers appear to be the same person or names are missing.",
    ))

    # 4. Report Date Sequence
    test_date_str = data.get("date_of_test")
    issue_date_str = data.get("report_issue_date")
    if _is_present(test_date_str) and _is_present(issue_date_str):
        try:
            for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    td = datetime.strptime(str(test_date_str).strip(), fmt)
                    break
                except ValueError:
                    td = None
            for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    id_ = datetime.strptime(str(issue_date_str).strip(), fmt)
                    break
                except ValueError:
                    id_ = None
            if td and id_:
                passed = id_ >= td
            else:
                passed = None
        except Exception:
            passed = None
    else:
        passed = None
    checks.append(_check(
        "Report Date Sequence", S,
        passed,
        f"Test: {test_date_str}, Issue: {issue_date_str}",
        "Issue date ≥ test date",
        f"Issue date ({issue_date_str}) is on or after test date ({test_date_str})." if passed is True
        else f"Issue date ({issue_date_str}) is before test date ({test_date_str})." if passed is False
        else "Cannot verify date sequence — dates missing or unparseable.",
    ))

    # 5–13. Photo and document presence checks
    photo_checks = [
        ("has_exterior_photos", "Exterior Unit Photos", "Exterior view photos (front, back, sides)"),
        ("has_connector_panel_photo", "Tuner Port Photo", "Connector panel photo showing tuner"),
        ("has_nameplate_photo", "Nameplate Label Photo", "Nameplate photo"),
        ("has_picture_settings_photos", "Picture Settings Photos", "Standard and brightest mode settings"),
        ("has_aspect_ratio_test_photo", "Aspect Ratio Test Photo", "Video aspect ratio during testing"),
        ("has_test_equipment_photo", "Test Equipment Photo", "Equipment used during testing"),
        ("has_test_setup_photo", "Test Environment Photo", "Testing setup photo"),
        ("has_schematic_drawing", "Electrical Circuit Schematic", "Schematic drawing of internals"),
        ("has_component_list", "Critical Component List", "Component list with specifications"),
    ]
    for field, name, desc in photo_checks:
        val = data.get(field)
        checks.append(_check(
            name, S,
            val is True, val,
            desc,
            f"{name}: present." if val is True
            else f"{name}: not found in document." if val is False
            else f"{name}: unable to verify (requires visual inspection).",
        ))

    return checks


# ── Main Entry Point ───────────────────────────────────────────────────────

def validate_all(data: dict) -> dict:
    """Run all validation checks against extracted TV test report data.

    Args:
        data: dict with keys matching the extraction schema.

    Returns:
        dict with:
            summary: {total, passed, failed, warnings}
            sections: list of section results
    """
    all_sections = [
        ("Section 1: Testing Laboratory", _validate_section1(data)),
        ("Section 2: Product Specification", _validate_section2(data)),
        ("Section 3: Energy Consumption (On Mode)", _validate_section3(data)),
        ("Section 4: Standby Mode", _validate_section4(data)),
        ("Section 5: Signatures & Appendices", _validate_section5(data)),
    ]

    total = 0
    passed = 0
    failed = 0
    warnings = 0

    sections_out = []
    for section_name, checks in all_sections:
        s_passed = sum(1 for c in checks if c["passed"] is True)
        s_failed = sum(1 for c in checks if c["passed"] is False)
        s_warn = sum(1 for c in checks if c["passed"] is None)
        total += len(checks)
        passed += s_passed
        failed += s_failed
        warnings += s_warn
        sections_out.append({
            "name": section_name,
            "checks": checks,
            "summary": {"total": len(checks), "passed": s_passed, "failed": s_failed, "warnings": s_warn},
        })

    return {
        "summary": {"total": total, "passed": passed, "failed": failed, "warnings": warnings},
        "sections": sections_out,
    }
