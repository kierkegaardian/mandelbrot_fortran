from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation


def is_correct_answer(correct: str, answer: str, answer_is_repeating: bool = False) -> bool:
    def normalize_money(value: str) -> str | None:
        cleaned = value.replace(" ", "").replace("$", "").replace(",", "")
        if not cleaned:
            return None
        try:
            decimal_value = Decimal(cleaned)
        except InvalidOperation:
            return None
        return f"{decimal_value.quantize(Decimal('0.01'))}"

    def reduce_fraction(num: int, den: int) -> tuple[int, int]:
        if den < 0:
            num = -num
            den = -den
        g = math.gcd(num, den)
        return (num // g, den // g)

    def norm_text(value: str) -> str:
        cleaned = value.replace(" ", "").replace("/", ":").replace("$", "").replace(",", "")
        lowered = cleaned.lower()
        return lowered.replace("remainder", "r")

    def norm_fraction(value: str) -> tuple[int, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        if " " in cleaned and "/" in cleaned:
            parts = cleaned.split()
            if len(parts) == 2 and "/" in parts[1]:
                try:
                    whole = int(parts[0])
                    frac_parts = parts[1].split("/")
                    if len(frac_parts) != 2:
                        return None
                    num = int(frac_parts[0])
                    den = int(frac_parts[1])
                except ValueError:
                    return None
                if den == 0:
                    return None
                total = whole * den + num
                return reduce_fraction(total, den)
        if "/" not in cleaned and ":" not in cleaned:
            return None
        cleaned = cleaned.replace(" ", "").replace(":", "/")
        parts = cleaned.split("/")
        if len(parts) != 2:
            return None
        try:
            num = int(parts[0])
            den = int(parts[1])
        except ValueError:
            return None
        if den == 0:
            return None
        return reduce_fraction(num, den)

    def norm_decimal_fraction(value: str) -> tuple[int, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        if "/" in cleaned or ":" in cleaned:
            return None
        try:
            dec = Decimal(cleaned)
        except InvalidOperation:
            return None
        tup = dec.as_tuple()
        digits = int("".join(str(d) for d in tup.digits) or "0")
        if tup.exponent >= 0:
            num = digits * (10 ** tup.exponent)
            den = 1
        else:
            den = 10 ** (-tup.exponent)
            num = digits
        if tup.sign:
            num = -num
        return reduce_fraction(num, den)

    def norm_repeating_decimal(value: str, repeat_flag: bool) -> tuple[int, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned.lower().endswith("r") and "(" not in cleaned:
            cleaned = cleaned[:-1]
            repeat_flag = True
        if "(" in cleaned and ")" in cleaned:
            return _parse_repeat_parens(cleaned)
        if not repeat_flag:
            return None
        return _parse_repeat_block(cleaned)

    def decimal_value(value: str) -> tuple[Decimal, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        if "/" in cleaned or ":" in cleaned:
            return None
        try:
            dec = Decimal(cleaned)
        except InvalidOperation:
            return None
        digits_after = max(0, -dec.as_tuple().exponent)
        return dec, digits_after

    def decimal_matches_fraction(value: str, fraction: tuple[int, int]) -> bool:
        dec_info = decimal_value(value)
        if dec_info is None:
            return False
        dec, digits_after = dec_info
        num, den = fraction
        frac_val = Decimal(num) / Decimal(den)
        if digits_after <= 0:
            return dec == frac_val
        tolerance = Decimal("0.5") * (Decimal(10) ** (-digits_after))
        return abs(dec - frac_val) <= tolerance

    def _parse_repeat_block(value: str) -> tuple[int, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        if "/" in cleaned or ":" in cleaned:
            return None
        sign = -1 if cleaned.startswith("-") else 1
        if cleaned[0] in "+-":
            cleaned = cleaned[1:]
        if "." not in cleaned:
            return None
        whole_str, frac_str = cleaned.split(".", 1)
        if not frac_str.isdigit() or not whole_str.isdigit():
            return None
        if not frac_str:
            return None
        whole = int(whole_str or "0")
        rep = int(frac_str)
        n = len(frac_str)
        den = (10**n) - 1
        num = whole * den + rep
        return reduce_fraction(sign * num, den)

    def _parse_repeat_parens(value: str) -> tuple[int, int] | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        sign = -1 if cleaned.startswith("-") else 1
        if cleaned[0] in "+-":
            cleaned = cleaned[1:]
        if "(" not in cleaned or ")" not in cleaned:
            return None
        prefix, rest = cleaned.split("(", 1)
        repeat_str, tail = rest.split(")", 1)
        if tail.strip():
            return None
        if not repeat_str.isdigit() or not repeat_str:
            return None
        if "." in prefix:
            whole_str, nonrep_str = prefix.split(".", 1)
        else:
            whole_str, nonrep_str = prefix, ""
        if whole_str and not whole_str.isdigit():
            return None
        if nonrep_str and not nonrep_str.isdigit():
            return None
        whole = int(whole_str or "0")
        nonrep = int(nonrep_str or "0")
        m = len(nonrep_str)
        n = len(repeat_str)
        rep = int(repeat_str)
        den = (10**m) * ((10**n) - 1)
        num = whole * den + nonrep * ((10**n) - 1) + rep
        return reduce_fraction(sign * num, den)

    if "$" in correct or "$" in answer:
        money_correct = normalize_money(correct)
        money_answer = normalize_money(answer)
        if money_correct is not None and money_answer is not None:
            return money_correct == money_answer

    frac_correct = norm_fraction(correct)
    frac_answer = norm_fraction(answer)
    if frac_correct is not None:
        if frac_answer is not None and frac_answer == frac_correct:
            return True
        dec_answer = norm_decimal_fraction(answer)
        if dec_answer is not None and dec_answer == frac_correct:
            return True
        rep_answer = norm_repeating_decimal(answer, answer_is_repeating)
        if rep_answer is not None and rep_answer == frac_correct:
            return True
        if decimal_matches_fraction(answer, frac_correct):
            return True
    if frac_answer is not None:
        dec_correct = norm_decimal_fraction(correct)
        if dec_correct is not None and dec_correct == frac_answer:
            return True
        rep_correct = norm_repeating_decimal(correct, False)
        if rep_correct is not None and rep_correct == frac_answer:
            return True
        if decimal_matches_fraction(correct, frac_answer):
            return True

    norm_correct = norm_text(correct)
    norm_answer = norm_text(answer)
    if "r" in norm_answer and "r" not in norm_correct:
        if norm_answer.endswith("r0") and norm_answer[:-2] == norm_correct:
            return True
    return norm_correct == norm_answer
