"""Сборка datasets/golden/blind.jsonl из размеченных примеров."""

import json
import sys
from pathlib import Path

import blind_types  # noqa: F401  (регистрирует примеры)
import blind_traps  # noqa: F401
import blind_complex  # noqa: F401
from blind_core import EXAMPLES

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("blind.jsonl")


def _has(fine: str, *words: str) -> bool:
    return any(w in fine for w in words)


def _trap_family(fine: str) -> str:
    if fine.startswith("mixed_"):
        return "trap_with_pii"
    if _has(fine, "public_figure", "film", "landmark", "book", "award", "fictional",
            "authors", "library"):
        return "trap_public_figure"
    if _has(fine, "common_noun", "tariff"):
        return "trap_common_word"
    if _has(fine, "company", "llc", "requisites", "head_office", "corporate", "ogrn",
            "swift", "office_on"):
        return "trap_organization"
    if _has(fine, "branch", "bank_office", "atm", "flagship", "office_leninsky"):
        return "trap_branch_address"
    if _has(fine, "city", "capital", "bank_history", "metro", "meeting_square"):
        return "trap_place"
    if _has(fine, "hotline", "short_number", "emergency", "contact_center"):
        return "trap_org_phone"
    if _has(fine, "policy", "explanation", "generic", "fee", "template", "masked_card"):
        return "trap_term_or_template"
    return "trap_numbers_dates"


def _complex_family(fine: str) -> str:
    if _has(fine, "log_line"):
        return "complex_log"
    if _has(fine, "json"):
        return "complex_json"
    if _has(fine, "table", "csv"):
        return "complex_table"
    if _has(fine, "dialog", "transcript", "chatbot", "operator_chat"):
        return "complex_dialogue"
    if _has(fine, "anketa", "bullets", "ocr", "block", "power_of_attorney"):
        return "complex_form"
    if _has(fine, "email", "sms", "ticket", "letter_foreign"):
        return "complex_email_sms"
    if _has(fine, "llm"):
        return "complex_llm_prompt"
    return "complex_paragraph"


def _combo_family(fine: str) -> str:
    if _has(fine, "last4", "no_card", "alone", "dialog"):
        return "combo_value_alone"
    return "combo_with_card"


_FORMAT_WORDS = (
    "format_", "iso", "dash", "dots", "no_sep", "no_space", "text_date", "text_words",
    "year", "digits_spaced", "grouped", "space_sep", "plus7", "eight", "seven", "local",
    "foreign", "mir19", "amex", "unionpay", "line_break", "obfuscated", "cyrillic",
    "plus_tag", "subdomain", "digits_underscore", "long_tld", "old_cyrillic", "letters",
    "single_digit", "gr_no_space", "six_digits", "leading_zero", "hyphenated",
    "middle_initial", "abbr", "historical", "colloquial", "value_first", "pinkod_joined",
    "pan_label", "english", "zelenograd", "house_letter", "comma_house", "no_service_words",
    "derevnya", "house_apt", "mkr", "stanitsa", "id_card", "rvp", "military", "birth_cert",
    "zagran", "vnzh", "parentheses", "angle_brackets", "trailing_period", "adjective",
    "dual", "country", "two_phones", "json", "descriptive", "new_old", "with_",
    "in_parentheses", "latin_code", "region", "index", "prospekt", "pushkin_street",
    "street_house", "district", "village", "city", "kogda", "pin_kod", "pin_ot",
    "russian_label", "labeled_cvc2", "full_name_label", "legacy", "cvv2",
)
_NAME_WORDS = ("non_slavic", "double_surname", "initials", "surname_only", "name_",
               "latin_in_russian", "two_persons")
_DECLENSION_WORDS = ("declension", "genitive", "dative", "instrumental", "prepositional",
                     "urozhenka", "grazhdan", "rodom_iz")


def coarse_variant(category: str, fine: str) -> tuple[str, str]:
    """Возвращает (variant, subvariant). Явное 'coarse:fine' в разметке имеет приоритет."""
    if ":" in fine:
        coarse, fine = fine.split(":", 1)
        return coarse, fine
    return _derive(category, fine), fine


def _derive(category: str, fine: str) -> str:
    if category == "TRAP":
        return _trap_family(fine)
    if category == "COMPLEX":
        return _complex_family(fine)
    if category == "COMBO":
        return _combo_family(fine)
    if _has(fine, "invalid_checksum", "luhn_invalid"):
        return "invalid_checksum_labeled"
    if _has(fine, "bare"):
        return "bare_value"
    if _has(fine, "llm"):
        return "llm_prompt"
    if _has(fine, "mixed_case"):
        return "mixed_case"
    if _has(fine, "upper"):
        return "upper_case"
    if _has(fine, "lower"):
        return "lower_case"
    if _has(fine, "separator", "numsign", "reversed_order", "abbr_ser", "series"):
        return "separator_words"
    if _has(fine, *_DECLENSION_WORDS):
        return "declension"
    if category == "PERSON" and _has(fine, *_NAME_WORDS):
        return "name_variation"
    if _has(fine, "label"):
        return "labeled"
    if _has(fine, *_FORMAT_WORDS):
        return "format_variation"
    return "in_sentence"


def main() -> None:
    rows = []
    for i, ex in enumerate(EXAMPLES, start=1):
        variant, subvariant = coarse_variant(ex["category"], ex["variant"])
        rows.append({
            "id": f"blind-{i:04d}",
            "category": ex["category"],
            "variant": variant,
            "subvariant": subvariant,
            "text": ex["text"],
            "pii": ex["pii"],
            "not_pii": ex["not_pii"],
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows -> {OUT}")
    if "--show-variants" in sys.argv:
        for row in rows:
            print(f"{row['category']:<20} {row['variant']:<26} {row['subvariant']}")


if __name__ == "__main__":
    main()
