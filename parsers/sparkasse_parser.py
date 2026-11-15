"""Parse Hamburger Sparkasse EUR statements into a pandas DataFrame."""
import argparse
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

import pandas as pd
import pdfplumber

COLUMNS = ['transaction date', 'expense amount', 'currency', 'expense description', 'location', 'bank']
AMOUNT = r'[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}'
TRANSACTION = re.compile(rf'^(\d{{2}}\.\d{{2}}\.\d{{4}})\s*(.+?)\s+({AMOUNT})$')
BALANCE = re.compile(rf'^(Kontostand am.*?|Übertrag:)\s+({AMOUNT})$')
HEADER = 'Datum Erläuterung Betrag EUR'
DEFAULT_DIRECTORY = Path(__file__).resolve().parents[1] / 'expenses' / 'sparkasse'


def money(value: str) -> Decimal:
    return Decimal(value.replace('.', '').replace(',', '.'))


def extract_location(description: str) -> str | None:
    """Read the city/country from card details, leaving unknown locations missing."""
    details = re.split(r'\s+\d{4}-\d{2}-\d{2}T', description, maxsplit=1)[0]
    parts = details.split('/')
    for index in range(len(parts) - 1, 1, -1):
        country = parts[index].strip().replace(' ', '')
        if re.fullmatch(r'[A-Z]{2}', country):
            city = parts[index - 1].strip()
            if city.isupper():
                city = city.replace(' ', '').title()
            else:
                city = re.sub(r'\b(\w+)\s+(\w{1,2})$', r'\1\2', city)
            return f'{city}, {country}' if city else None
    return None


class SparkasseParser:
    bank = 'Sparkasse'

    def supports(self, pages: list[str]) -> bool:
        return bool(pages) and all(marker in pages[0] for marker in ('Hamburger Sparkasse', 'Kontoauszug', HEADER))

    def parse(self, pages: list[str]) -> pd.DataFrame:
        """Return booking dates and signed amounts; validate page balances.

        Debits are negative and credits positive. Attachments are excluded
        because their charges already appear in the transaction table.
        """
        if not self.supports(pages):
            raise ValueError('Unsupported Sparkasse statement layout')
        records = []
        previous_balance = None
        closed = False
        for page_number, page in enumerate(pages, 1):
            if HEADER not in page:
                if any(TRANSACTION.fullmatch(line.strip()) for line in page.splitlines()):
                    raise ValueError(f'Unrecognized transaction page {page_number}')
                continue
            if closed:
                raise ValueError('Transaction table after closing balance')
            body = page.split(HEADER, 1)[1].split('Hamburger Sparkasse AG', 1)[0]
            balances = []
            page_records = []
            current = None
            description = []

            def finish() -> None:
                nonlocal current
                if current is None:
                    return
                date, label, amount = current.groups()
                details = ' '.join(description)
                page_records.append({
                    'transaction date': datetime.strptime(date, '%d.%m.%Y'),
                    'expense amount': money(amount),
                    'currency': 'EUR',
                    'expense description': ' '.join(filter(None, (label, details))),
                    'location': extract_location(details),
                    'bank': self.bank,
                })
                current = None
                description.clear()

            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue
                balance = BALANCE.fullmatch(line)
                transaction = TRANSACTION.fullmatch(line)
                if balance:
                    finish()
                    balances.append((balance[1], money(balance[2])))
                elif transaction:
                    finish()
                    current = transaction
                elif current is not None:
                    description.append(line)
                elif len(balances) < 2:
                    raise ValueError(f'Unrecognized table row on page {page_number}: {line}')
            finish()
            if len(balances) != 2:
                raise ValueError(f'Expected two balances on page {page_number}')
            (opening_label, opening), (closing_label, closing) = balances
            if previous_balance is None:
                if not opening_label.startswith('Kontostand am'):
                    raise ValueError('Missing opening balance')
            elif opening != previous_balance:
                raise ValueError(f'Carry-forward mismatch on page {page_number}')
            total = sum((row['expense amount'] for row in page_records), Decimal(0))
            if opening + total != closing:
                raise ValueError(f'Balance reconciliation failed on page {page_number}')
            previous_balance = closing
            closed = closing_label.startswith('Kontostand am')
            records.extend(page_records)
        if previous_balance is None or not closed:
            raise ValueError('Incomplete statement: missing closing balance')
        frame = pd.DataFrame.from_records(records, columns=COLUMNS)
        frame['transaction date'] = pd.to_datetime(frame['transaction date'])
        return frame

    def parse_pdf(self, path: str | Path) -> pd.DataFrame:
        with pdfplumber.open(path) as pdf:
            return self.parse([page.extract_text() or '' for page in pdf.pages])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', nargs='?', type=Path, help='PDF to parse; defaults to the first Sparkasse PDF')
    args = parser.parse_args()
    path = args.pdf
    if path is None:
        files = sorted(p for p in DEFAULT_DIRECTORY.iterdir() if p.suffix.lower() == '.pdf')
        if not files:
            parser.error(f'No PDFs found in {DEFAULT_DIRECTORY}')
        path = files[0]
    frame = SparkasseParser().parse_pdf(path)
    print(frame.head().to_string(index=False))


if __name__ == '__main__':
    main()
