#!/usr/bin/env python3
"""
Make the destination/country field optional in the booking modal.

Before: client-side block alerted "Please add the country..." and refused to
submit when parseCountries() returned an empty list. Cities (e.g. "Rio de
Janiero") or blank destinations stalled the inquiry on step 1.

After: submission proceeds with an empty country_names array when the user
typed nothing parseable; summary shows "No idea where should I go" instead of
"To be confirmed with Butler" for the Destination row.

Idempotent: skips files that no longer contain the old block.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "zoho-inject" / "_modal-snippet.js",
    ROOT / "zoho-inject" / "inject-home-v3.js",
    ROOT / "zoho-inject" / "inject-advisor-v3.js",
    ROOT / "zoho-inject" / "inject-concierge-v3.js",
    ROOT / "zoho-inject" / "inject-trip-planning-v3.js",
    ROOT / "zoho-inject" / "inject-supplier-code-v3.js",
    ROOT / "proposed" / "home.html",
    ROOT / "proposed" / "concierge.html",
    ROOT / "proposed" / "trip-planning.html",
    ROOT / "proposed" / "travel-advisor.html",
    ROOT / "proposed" / "supplier-code.html",
]

# Two dash flavours appear in the alert across files; handle both.
OLD_BLOCKS = [
    """    var countryNames = parseCountries(i.Destination || '');
    if (!countryNames.length) {
      alert('Please add the country (or countries) for your trip in the destination field - e.g. \"Japan\" or \"Italy, France\".');
      showStep(1);
      var dest = document.getElementById('bbm-dest');
      if (dest) {
        dest.focus();
        var row = dest.closest('.bb-modal__row');
        if (row) row.classList.add('has-error');
      }
      return;
    }
""",
    """    var countryNames = parseCountries(i.Destination || '');
    if (!countryNames.length) {
      alert('Please add the country (or countries) for your trip in the destination field \\u2014 e.g. \"Japan\" or \"Italy, France\".');
      showStep(1);
      var dest = document.getElementById('bbm-dest');
      if (dest) {
        dest.focus();
        var row = dest.closest('.bb-modal__row');
        if (row) row.classList.add('has-error');
      }
      return;
    }
""",
]

NEW_BLOCK = """    var countryNames = parseCountries(i.Destination || '');
"""

OLD_SUMMARY = "['Destination', i.Destination || 'To be confirmed with Butler'],"
NEW_SUMMARY = "['Destination', i.Destination || 'No idea where should I go'],"


def patch(path: pathlib.Path) -> str:
    text = path.read_text()
    orig = text

    matched_block = False
    for old in OLD_BLOCKS:
        if old in text:
            text = text.replace(old, NEW_BLOCK, 1)
            matched_block = True
            break

    if OLD_SUMMARY in text:
        text = text.replace(OLD_SUMMARY, NEW_SUMMARY, 1)
        summary_changed = True
    else:
        summary_changed = False

    if text == orig:
        return "SKIP (already patched or unrecognised)"

    path.write_text(text)
    parts = []
    if matched_block:
        parts.append("block removed")
    if summary_changed:
        parts.append("summary updated")
    return "OK: " + ", ".join(parts)


def main():
    for f in FILES:
        if not f.exists():
            print(f"MISS {f.name}")
            continue
        print(f"{f.relative_to(ROOT)}: {patch(f)}")


if __name__ == "__main__":
    main()
