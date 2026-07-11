import re
from datetime import datetime

from app.schemas.receipt import Receipt


_AMOUNT_RE = re.compile(r"(?<!\d)(?:\$\s*)?(\d{1,6}(?:\.\d{2})?)(?!\d)")
_DATE_PATTERNS = ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y")


class ReceiptParserService:
    """Conservative rule-based parser used before optional AI enrichment."""

    def extract(self, text: str) -> Receipt:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        merchant = self._merchant(lines)
        purchase_date, date_confidence = self._date(text)
        total, total_confidence = self._labeled_amount(lines, ("grand total", "amount due", "total"))
        subtotal, _ = self._labeled_amount(lines, ("subtotal", "sub total"))
        tax, _ = self._labeled_amount(lines, ("tax",))
        tip, _ = self._labeled_amount(lines, ("tip", "gratuity"))

        if total is None:
            amounts = [float(match) for match in _AMOUNT_RE.findall(text)]
            total = max(amounts, default=0.0)
            total_confidence = 0.45 if amounts else 0.1

        return Receipt(
            merchant=merchant,
            purchase_date=purchase_date,
            subtotal=subtotal,
            tax=tax,
            tip=tip,
            total=total,
            source_text=text,
            confidence={
                "merchant": 0.65 if lines else 0.1,
                "purchase_date": date_confidence,
                "total": total_confidence,
            },
        )

    @staticmethod
    def _merchant(lines: list[str]) -> str:
        for line in lines[:4]:
            if not _AMOUNT_RE.fullmatch(line.replace(",", "")) and len(line) <= 80:
                return line.title()
        return "Unknown merchant"

    @staticmethod
    def _date(text: str):
        candidates = re.findall(
            r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b",
            text,
        )
        for candidate in candidates:
            for pattern in _DATE_PATTERNS:
                try:
                    return datetime.strptime(candidate, pattern).date(), 0.85
                except ValueError:
                    continue
        return None, 0.1

    @staticmethod
    def _labeled_amount(lines: list[str], labels: tuple[str, ...]):
        for line in reversed(lines):
            lowered = line.lower()
            if any(label in lowered for label in labels):
                matches = _AMOUNT_RE.findall(line.replace(",", ""))
                if matches:
                    return float(matches[-1]), 0.9
        return None, 0.1
