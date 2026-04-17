"""Generate DOCX contracts from Word templates by replacing [placeholder] markers."""

import re
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from docx import Document

from app.core.config import settings
from app.services.storage import storage_service

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "contracts_examples"
PSA_TEMPLATE = TEMPLATES_DIR / "шаблон_договор_купли_продажи.docx"
LA_TEMPLATE = TEMPLATES_DIR / "шаблон_договор_лизинга.docx"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num_to_words(n: float, currency: str = "BYN") -> str:
    """Russian number-to-words for contract sums."""
    n = round(n, 2)
    int_part = int(n)
    frac = round((n - int_part) * 100)

    if int_part == 0:
        return f"ноль {_currency_word(currency)} {frac:02d} коп."

    groups: list[int] = []
    remaining = int_part
    while remaining > 0:
        groups.append(remaining % 1000)
        remaining //= 1000

    ones = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    ones_f = ["", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    teens = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
             "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
    tens = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят",
            "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
    hundreds = ["", "сто", "двести", "триста", "четыреста", "пятьсот",
                "шестьсот", "семьсот", "восемьсот", "девятьсот"]

    def _group_words(g: int, feminine: bool = False) -> str:
        parts: list[str] = []
        h = g // 100
        t = (g % 100) // 10
        o = g % 10
        if h:
            parts.append(hundreds[h])
        if t == 1:
            parts.append(teens[o])
        else:
            if t:
                parts.append(tens[t])
            if o:
                parts.append((ones_f if feminine else ones)[o])
        return " ".join(parts)

    scale_names = [
        ("", "", "", False),
        ("тысяча", "тысячи", "тысяч", True),
        ("миллион", "миллиона", "миллионов", False),
        ("миллиард", "миллиарда", "миллиардов", False),
    ]

    result_parts: list[str] = []
    for i, g in enumerate(groups):
        if g == 0:
            continue
        sn = scale_names[i] if i < len(scale_names) else ("", "", "", False)
        w = _group_words(g, sn[3])
        o = g % 10
        t = (g % 100) // 10
        if sn[0]:
            if t == 1:
                suffix = sn[2]
            elif o == 1:
                suffix = sn[0]
            elif 2 <= o <= 4:
                suffix = sn[1]
            else:
                suffix = sn[2]
            w = f"{w} {suffix}"
        result_parts.append(w)

    result_parts.reverse()
    text = " ".join(result_parts).strip()
    cw = _currency_word(currency)
    return f"{text} {cw} {frac:02d} коп."


def _currency_word(code: str) -> str:
    mapping = {"BYN": "руб.", "USD": "долл. США", "EUR": "евро", "RUB": "росс. руб."}
    return mapping.get(code, "руб.")


def _format_date(d) -> str:
    if d is None:
        return "___________"
    if hasattr(d, "strftime"):
        months = [
            "", "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        return f"{d.day} {months[d.month]} {d.year} г."
    return str(d)


def _format_date_dots(d) -> str:
    """Format date as dd.mm.yyyy"""
    if d is None:
        return "___________"
    if hasattr(d, "strftime"):
        return d.strftime("%d.%m.%Y")
    return str(d)


def _safe(val, default="___________") -> str:
    if val is None or val == "":
        return default
    return str(val)


# ---------------------------------------------------------------------------
# User data extractors (support company / entrepreneur / individual)
# ---------------------------------------------------------------------------

def _user_name(u) -> str:
    if not u:
        return ""
    if u.company:
        return u.company.company_name or ""
    if u.entrepreneur:
        return u.entrepreneur.full_name or ""
    if u.individual:
        return u.individual.full_name or ""
    return ""


def _legal_form(u) -> str:
    if u and u.company:
        return u.company.legal_form or ""
    return ""


def _legal_form_and_name(u) -> str:
    """Full representation depending on user type: company / IE / individual."""
    if not u:
        return ""
    if u.company:
        lf = u.company.legal_form or ""
        name = u.company.company_name or ""
        return f'{lf} "{name}"' if lf else name
    if u.entrepreneur:
        return f'ИП {u.entrepreneur.full_name or ""}'
    if u.individual:
        return f'Физическое лицо {u.individual.full_name or ""}'
    return ""


def _director_or_name(u) -> str:
    """Director for company, full_name for IE/individual."""
    if not u:
        return ""
    if u.company:
        return u.company.director_name or ""
    if u.entrepreneur:
        return u.entrepreneur.full_name or ""
    if u.individual:
        return u.individual.full_name or ""
    return ""


def _unp(u) -> str:
    if not u:
        return ""
    if u.company:
        return u.company.unp or ""
    if u.entrepreneur:
        return u.entrepreneur.unp or ""
    return ""


def _legal_address(u) -> str:
    if not u:
        return ""
    if u.company:
        return u.company.legal_address or ""
    if u.entrepreneur:
        return u.entrepreneur.legal_address or ""
    if u.individual:
        return u.individual.registration_address or ""
    return ""


def _postal_address(u) -> str:
    if not u:
        return ""
    if u.company:
        return u.company.postal_address or u.company.legal_address or ""
    if u.entrepreneur:
        return u.entrepreneur.postal_address or u.entrepreneur.legal_address or ""
    if u.individual:
        return u.individual.registration_address or ""
    return ""


def _contact_phone(u) -> str:
    if not u:
        return ""
    return next((c.value for c in (u.contacts or []) if c.type.value == "phone"), "")


def _contact_email(u) -> str:
    if not u:
        return ""
    return next((c.value for c in (u.contacts or []) if c.type.value == "email"), "")


def _first_bank(u):
    if u and u.bank_accounts:
        return u.bank_accounts[0]
    return None


def _passport_id(u) -> str:
    if u and u.individual:
        return u.individual.passport_id or ""
    return ""


# ---------------------------------------------------------------------------
# DOCX replacement engine
# ---------------------------------------------------------------------------

def _replace_in_paragraph(paragraph, replacements: dict[str, str]) -> None:
    full_text = paragraph.text
    if "[" not in full_text:
        return

    new_text = full_text
    for key, value in replacements.items():
        new_text = new_text.replace(f"[{key}]", str(value))

    if new_text == full_text:
        return

    if not paragraph.runs:
        return

    for run in paragraph.runs:
        run.text = ""
    paragraph.runs[0].text = new_text


def _replace_in_table(table, replacements: dict[str, str]) -> None:
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                _replace_in_paragraph(paragraph, replacements)


def _replace_in_table_column(table, col_idx: int, replacements: dict[str, str]) -> None:
    """Replace placeholders only in a specific column of a table."""
    for row in table.rows:
        if col_idx < len(row.cells):
            cell = row.cells[col_idx]
            for paragraph in cell.paragraphs:
                _replace_in_paragraph(paragraph, replacements)


def _replace_in_doc(doc: Document, replacements: dict[str, str]) -> None:
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, replacements)
    for table in doc.tables:
        _replace_in_table(table, replacements)

    for section in doc.sections:
        for header in (section.header, section.first_page_header, section.even_page_header):
            if header and header.is_linked_to_previous is False:
                for p in header.paragraphs:
                    _replace_in_paragraph(p, replacements)
        for footer in (section.footer, section.first_page_footer, section.even_page_footer):
            if footer and footer.is_linked_to_previous is False:
                for p in footer.paragraphs:
                    _replace_in_paragraph(p, replacements)


# ---------------------------------------------------------------------------
# PSA (Договор купли-продажи)
# ---------------------------------------------------------------------------

def _build_common_vehicle_replacements(contract, vehicle, vat_rate: float, currency: str) -> dict[str, str]:
    """Vehicle + financial placeholders shared between PSA body and tables."""
    price = vehicle.price if vehicle else 0
    quantity = contract.quantity or 1
    total_price = price * quantity
    vat_amount = round(total_price * vat_rate / 100, 2)
    price_without_vat = round(total_price - vat_amount, 2)
    half_price = round(total_price / 2, 2)

    condition_raw = vehicle.condition if vehicle else "used"
    condition = "Новый" if condition_raw == "new" else "Б/у"

    condition_full_new = ("Товар является новым. В связи с этим Продавец предоставляет "
                          "гарантию на передаваемый товар согласно условиям.")
    condition_full_used = ("Товар является бывшим в эксплуатации и передается Покупателю в том состоянии, "
                           "в котором он фактически находится на момент его передачи. В связи с этим Продавец "
                           "не предоставляет гарантию на передаваемый товар, обмену и возврату товар не подлежит.")
    condition_full = condition_full_new if condition_raw == "new" else condition_full_used

    warranty_new = "Продавец несет ответственность за скрытые недостатки товара."
    warranty_used = ("Продавец не несет ответственности за скрытые недостатки товара "
                     "в связи с тем, что товар является бывшим в эксплуатации.")
    warranty_text = warranty_new if condition_raw == "new" else warranty_used

    three_days = (contract.signing_date + timedelta(days=3)) if contract.signing_date else None

    return {
        "состояние": condition,
        "состояние товара полностью": condition_full,
        "тип ТС": _safe(vehicle.vehicle_type if vehicle else None, "транспортное средство"),
        "наименование полностью": _safe(vehicle.name if vehicle else None),
        "год выпуска": _safe(vehicle.release_year if vehicle else None),
        "VIN-номер": _safe(vehicle.vin if vehicle else None),
        "№техпаспорта": _safe(contract.tech_passport_number),
        "дата выдачи": _format_date_dots(contract.tech_passport_date),
        "кол-во": str(quantity),
        "цена в объявлении": f"{total_price:.2f}",
        "цена в объявлении – сумма НДС": f"{price_without_vat:.2f}",
        "валюта": _safe(currency, "BYN"),
        "число НДС": str(int(vat_rate)),
        "число НДС на момент подписания": str(int(vat_rate)),
        "сумма НДС": f"{vat_amount:.2f}",
        "сумма НДС словами": _num_to_words(vat_amount, currency),
        "сумма словами": _num_to_words(total_price, currency),
        "цена из объявления словами": _num_to_words(total_price, currency),
        "половина от полной цены в объявлении": f"{half_price:.2f}",
        "половина от полной цены словами": _num_to_words(half_price, currency),
        "способ оплаты": "безналичный расчет",
        "дата, спустя три дня со дня формирования договора": _format_date_dots(three_days),
        ("Товар является бывшим в эксплуатации и передается Покупателю в том состоянии, "
         "в котором он фактически находится на момент его передачи. В связи с этим Продавец "
         "не предоставляет гарантию на передаваемый товар, обмену и возврату товар не подлежит. "
         "ИЛИ: Товар является новым. В связи с этим Продавец предоставляет гарантию на "
         "передаваемый товар согласно условиям."): condition_full,
        ("Продавец не несет ответственности за скрытые недостатки товара в связи с тем, "
         "что товар является бывшим в эксплуатации. ИЛИ: Продавец несет ответственность "
         "за скрытые недостатки товара."): warranty_text,
    }


def _build_user_replacements(u, prefix: str = "") -> dict[str, str]:
    """Generic placeholders for a user used in tables and body text.
    prefix is unused for shared placeholders like [УНП], [IBAN], etc.
    """
    bank = _first_bank(u)
    return {
        "Организационно-правовая форма": _legal_form(u),
        "организ-прав. форма": _legal_form(u),
        "Название компании": _user_name(u),
        "название компании": _user_name(u),
        "УНП": _unp(u),
        "юридический адрес": _legal_address(u),
        "IBAN": _safe(bank.iban if bank else None),
        "название банка": _safe(bank.bank_name if bank else None),
        "SWIFT": _safe(bank.swift if bank else None, ""),
        "BIC": _safe(bank.bic if bank else None, ""),
        "номер телефона": _contact_phone(u),
        "электронная почта": _contact_email(u),
        "ФИО директора": _director_or_name(u),
    }


def generate_psa_document(contract, vehicle, supplier_user, lessor_user, lessee_user) -> BytesIO:
    doc = Document(str(PSA_TEMPLATE))

    vat_rate = contract.vat_rate or 20
    currency = contract.currency or "BYN"

    # --- Build the "global" replacements applied to paragraphs ---
    # In the PSA body text, [Организационно-правовая форма], [Название компании], [ФИО директора]
    # in the header refer to Supplier (Продавец) first, then Lessor (Покупатель) second.
    # We handle these via table-specific processing.

    # Paragraphs: supplier-centric for "Продавец" lines, lessor-centric for "Покупатель" lines.
    # Since the template re-uses placeholders like [Организационно-правовая форма] for both parties
    # in paragraphs P3 (Продавец) and P4 (Покупатель), we must process paragraphs one-by-one.

    common_repl = {
        "номер ДКП": _safe(contract.contract_number),
        "год подписания": str(contract.signing_date.year) if contract.signing_date else "____",
        "город подписания": _safe(contract.signing_city),
        "дата подписания": _format_date(contract.signing_date),
    }
    common_repl.update(_build_common_vehicle_replacements(contract, vehicle, vat_rate, currency))

    supplier_repl = _build_user_replacements(supplier_user)
    lessor_repl = _build_user_replacements(lessor_user)

    # Specific named placeholders
    common_repl["ФИО директора поставщика"] = _director_or_name(supplier_user)
    common_repl["ФИО директора продавца"] = _director_or_name(supplier_user)
    common_repl["ФИО директора лизингодателя"] = _director_or_name(lessor_user)
    common_repl["ФИО директора лизингополучателя"] = _director_or_name(lessee_user)
    common_repl["юридический адрес поставщика"] = _legal_address(supplier_user)

    # [Организационно-правовая форма и Название компании] = lessee in context of "Согласовано с Лизингополучателем"
    common_repl["Организационно-правовая форма и Название компании"] = _legal_form_and_name(lessee_user)

    # --- Process paragraphs with context awareness ---
    # Track whether we're in Продавец or Покупатель context
    for para in doc.paragraphs:
        text = para.text
        if "[" not in text:
            continue

        # First replace common (always safe) placeholders
        _replace_in_paragraph(para, common_repl)

        # Now handle the ambiguous user-specific ones based on context
        text = para.text
        if "[" not in text:
            continue

        if "Продавец" in text or "Продавца" in text:
            _replace_in_paragraph(para, supplier_repl)
        elif "Покупатель" in text or "Покупателя" in text:
            _replace_in_paragraph(para, lessor_repl)
        elif "Лизингополучатель" in text:
            lessee_repl = _build_user_replacements(lessee_user)
            _replace_in_paragraph(para, lessee_repl)
        else:
            _replace_in_paragraph(para, supplier_repl)

    # --- Process tables ---
    for ti, table in enumerate(doc.tables):
        # TABLE 0, 5, 8: city/date (1x2) - common replacements
        # TABLE 1, 6, 9: vehicle data (2x8) - common replacements
        # TABLE 2: ПОКУПАТЕЛЬ details (4x2) - lessor data
        # TABLE 3: ПРОДАВЕЦ details (4x2) - supplier data
        # TABLE 4, 7: signatures with ПРОДАВЕЦ/ПОКУПАТЕЛЬ (col 0=supplier, col 1=lessor)
        # TABLE 10: 3-col table (col 0=labels, col 1=ПРОДАВЕЦ/supplier, col 2=ПОКУПАТЕЛЬ/lessor)
        # TABLE 11: last signatures table

        # First apply common replacements to all tables
        _replace_in_table(table, common_repl)

        # Detect table type by content
        first_cell = table.rows[0].cells[0].text if table.rows and table.rows[0].cells else ""
        cols = len(table.columns) if table.rows else 0
        rows = len(table.rows)

        # Check if this is the "ПОКУПАТЕЛЬ" details table (4 rows, 2 cols, first row = "Наименование:")
        if rows == 4 and cols == 2 and "Наименование" in first_cell:
            # Need to determine if this is the first (ПОКУПАТЕЛЬ=lessor) or second (ПРОДАВЕЦ=supplier)
            # In the document, TABLE 2 (after "ПОКУПАТЕЛЬ:") uses lessor data
            # TABLE 3 (after "ПРОДАВЕЦ:") uses supplier data
            # We check which section header appeared before this table
            # Simpler approach: check if it still has unresolved placeholders and apply
            _replace_in_table(table, lessor_repl)

        # Check for 3-column table with ПРОДАВЕЦ/ПОКУПАТЕЛЬ headers
        if cols == 3 and rows >= 5:
            header_row = table.rows[0]
            col1_text = header_row.cells[1].text if len(header_row.cells) > 1 else ""
            col2_text = header_row.cells[2].text if len(header_row.cells) > 2 else ""
            if "ПРОДАВЕЦ" in col1_text or "ПОКУПАТЕЛЬ" in col2_text:
                _replace_in_table_column(table, 1, supplier_repl)
                _replace_in_table_column(table, 2, lessor_repl)

        # Signature tables with ПРОДАВЕЦ col 0, ПОКУПАТЕЛЬ col 1
        if cols == 2 and rows > 5:
            first_row_c0 = table.rows[0].cells[0].text if table.rows[0].cells else ""
            first_row_c1 = table.rows[0].cells[1].text if len(table.rows[0].cells) > 1 else ""
            if "ПРОДАВЕЦ" in first_row_c0 or "ПОКУПАТЕЛЬ" in first_row_c1:
                _replace_in_table_column(table, 0, supplier_repl)
                _replace_in_table_column(table, 1, lessor_repl)
                lessee_repl_table = _build_user_replacements(lessee_user)
                _replace_in_table(table, lessee_repl_table)

        # The last small table (signatures: Директор / Директор лизинговой компании)
        if cols == 2 and rows <= 3:
            first_row_c1 = table.rows[0].cells[1].text if len(table.rows[0].cells) > 1 else ""
            if "лизинговой" in first_row_c1.lower():
                _replace_in_table_column(table, 0, supplier_repl)
                _replace_in_table_column(table, 1, lessor_repl)

    # Second pass: catch any remaining unresolved placeholders in tables
    # TABLE 2 is ПОКУПАТЕЛЬ (lessor), TABLE 3 is ПРОДАВЕЦ (supplier)
    # We need precise table index handling. Let's iterate again.
    _resolve_remaining_psa_tables(doc, supplier_repl, lessor_repl)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _resolve_remaining_psa_tables(doc: Document, supplier_repl: dict, lessor_repl: dict) -> None:
    """Second pass for PSA: find 4-row detail tables that still have placeholders."""
    # In the PSA, after paragraph "ПОКУПАТЕЛЬ:" comes a 4-row table for lessor
    # After "ПРОДАВЕЦ:" comes a 4-row table for supplier
    # We find them by checking preceding paragraph text

    # Build a combined element order from the document body
    body = doc.element.body
    prev_para_text = ""
    for elem in body:
        # Check if it's a paragraph
        if elem.tag.endswith('}p'):
            prev_para_text = elem.text or ""
            # Gather full text from all runs
            full_text = ""
            for child in elem.iter():
                if child.text:
                    full_text += child.text
            prev_para_text = full_text

        # Check if it's a table
        if elem.tag.endswith('}tbl'):
            # Find the matching table object
            for table in doc.tables:
                if table._tbl is elem:
                    has_placeholders = any(
                        "[" in cell.text
                        for row in table.rows
                        for cell in row.cells
                    )
                    if not has_placeholders:
                        break

                    rows = len(table.rows)
                    cols = len(table.columns) if table.rows else 0

                    if rows == 4 and cols == 2:
                        if "ПОКУПАТЕЛЬ" in prev_para_text:
                            _replace_in_table(table, lessor_repl)
                        elif "ПРОДАВЕЦ" in prev_para_text:
                            _replace_in_table(table, supplier_repl)
                    break


# ---------------------------------------------------------------------------
# LA (Договор лизинга)
# ---------------------------------------------------------------------------

def generate_la_document(contract, vehicle, lessor_user, lessee_user, supplier_user=None) -> BytesIO:
    doc = Document(str(LA_TEMPLATE))

    vat_rate = contract.vat_rate or 20
    currency = contract.currency or "BYN"
    price = vehicle.price if vehicle else 0
    total = contract.total_amount or 0
    vat_on_total = round(total * vat_rate / 100, 2)
    vat_on_price = round(price * vat_rate / 100, 2)
    price_without_vat = round(price - vat_on_price, 2)

    lessor_bank = _first_bank(lessor_user)
    lessee_bank = _first_bank(lessee_user)

    condition_raw = vehicle.condition if vehicle else "used"
    condition = "Новый" if condition_raw == "new" else "Б/у"

    # Build supplier line for paragraph 17 (Продавец Предмета лизинга)
    supplier_line = ""
    if supplier_user:
        if supplier_user.company:
            lf = supplier_user.company.legal_form or ""
            cn = supplier_user.company.company_name or ""
            unp = supplier_user.company.unp or ""
            supplier_line = f'{lf} "{cn}", УНП – {unp}'
        elif supplier_user.entrepreneur:
            fn = supplier_user.entrepreneur.full_name or ""
            unp = supplier_user.entrepreneur.unp or ""
            supplier_line = f'ИП "{fn}", УНП – {unp}'
        elif supplier_user.individual:
            fn = supplier_user.individual.full_name or ""
            pid = supplier_user.individual.passport_id or ""
            supplier_line = f'Физическое лицо "{fn}", идентификационный номер паспорта – {pid}'

    # Replacements dict
    repl: dict[str, str] = {
        "номер договора лизинга": _safe(contract.contract_number),
        "номер-договора": _safe(contract.contract_number),
        "город подписания": _safe(contract.signing_city),
        "дата подписания": _format_date(contract.signing_date),
        "дата окончания срока": _format_date(contract.end_date),
        "валюта": _safe(currency, "BYN"),
        "текущий НДС": str(int(vat_rate)),
        "число НДС на момент подписания": str(int(vat_rate)),
        "кол-во": str(contract.quantity or 1),
        "тип ТС": _safe(vehicle.vehicle_type if vehicle else None, "транспортное средство"),
        "название полностью": _safe(vehicle.name if vehicle else None),
        "год выпуска": _safe(vehicle.release_year if vehicle else None),
        "VIN номер": _safe(vehicle.vin if vehicle else None),
        "состояние": condition,

        "цена в объявлении": f"{price:.2f}",
        "цена в объявлении – сумма НДС": f"{price_without_vat:.2f}",
        "сумма НДС": f"{vat_on_price:.2f}",
        "сумма договора лизинга": f"{total:.2f}",
        "число": f"{total:.2f}",
        "число словами": _num_to_words(total, currency),
        "число суммы договора лизинга словами": _num_to_words(total, currency),
        "сумма НДС от договора лизинга": f"{vat_on_total:.2f}",
        "сумма НДС от договора лизинга словами": _num_to_words(vat_on_total, currency),

        "юридический адрес лизингодателя": _legal_address(lessor_user),
        "юридический адрес лизингополучателя": _legal_address(lessee_user),
    }

    # Lessor data
    repl["Название компании лизингодателя"] = _user_name(lessor_user)
    repl["IBAN"] = _safe(lessor_bank.iban if lessor_bank else None)
    repl["название банка"] = _safe(lessor_bank.bank_name if lessor_bank else None)
    repl["BIC"] = _safe(lessor_bank.bic if lessor_bank else None, "")
    repl["SWIFT"] = _safe(lessor_bank.swift if lessor_bank else None, "")

    # --- Process paragraphs with context ---
    # P3: Лизингодатель header
    # P4: Лизингополучатель header
    # P7-P8: ИНФОРМАЦИЯ О ЛИЗИНГОПОЛУЧАТЕЛЕ block
    # P9-P11: ИНФОРМАЦИЯ О ЛИЗИНГОДАТЕЛЕ block
    # P17: Supplier line
    # P28-P30: signatures (ЛИЗИНГОДАТЕЛЬ / ЛИЗИНГОПОЛУЧАТЕЛЬ)

    lessor_header_repl = {
        "Организационно правовая форма": _legal_form(lessor_user),
        "Название компании": _user_name(lessor_user),
        "ФИО директора": _director_or_name(lessor_user),
        "УНП": _unp(lessor_user),
    }
    lessee_header_repl = {
        "Организационно правовая форма": _legal_form(lessee_user) if lessee_user and lessee_user.company else "",
        "Название компании": _user_name(lessee_user),
        "ФИО директора": _director_or_name(lessee_user),
        "ФИО": _director_or_name(lessee_user),
        "УНП": _unp(lessee_user),
    }

    # Info block replacements for Лизингополучатель
    lessee_info = _build_la_info_block(lessee_user)
    lessor_info = _build_la_info_block(lessor_user)

    in_lessee_info = False
    in_lessor_info = False

    for para in doc.paragraphs:
        text = para.text

        if "ИНФОРМАЦИЯ О ЛИЗИНГОПОЛУЧАТЕЛЕ" in text:
            in_lessee_info = True
            in_lessor_info = False
            continue
        if "ИНФОРМАЦИЯ О ЛИЗИНГОДАТЕЛЕ" in text:
            in_lessor_info = True
            in_lessee_info = False
            continue
        if "ПРЕДМЕТ ДОГОВОРА" in text:
            in_lessee_info = False
            in_lessor_info = False

        if "[" not in text:
            continue

        _replace_in_paragraph(para, repl)
        text = para.text
        if "[" not in text:
            continue

        if in_lessee_info:
            _replace_in_paragraph(para, lessee_info)
        elif in_lessor_info:
            _replace_in_paragraph(para, lessor_info)
        elif "Лизингодатель" in text and "Лизингополучатель" not in text:
            _replace_in_paragraph(para, lessor_header_repl)
        elif "Лизингополучатель" in text:
            _replace_in_paragraph(para, lessee_header_repl)
        elif "Продавца" in text or "Продавец" in text:
            # Supplier mention in lease agreement
            if supplier_user:
                sup_repl = {
                    "Организационно правовая форма": _legal_form(supplier_user),
                    "Название компании": _user_name(supplier_user),
                    "УНП": _unp(supplier_user),
                }
                _replace_in_paragraph(para, sup_repl)
        else:
            _replace_in_paragraph(para, lessor_header_repl)

    # --- Process tables ---
    for table in doc.tables:
        _replace_in_table(table, repl)

        cols = len(table.columns) if table.rows else 0
        rows = len(table.rows)

        # TABLE 2: Реквизиты для перечисления платежа (lessor bank info)
        if rows == 4 and cols == 2:
            first_text = table.rows[0].cells[0].text if table.rows[0].cells else ""
            if "ЦЕНА ДОГОВОРА" in first_text:
                lessor_bank_repl = {
                    "Организационно правовая форма": _legal_form(lessor_user),
                    "Название компании лизингодателя": _user_name(lessor_user),
                    "УНП": _unp(lessor_user),
                    "IBAN": _safe(lessor_bank.iban if lessor_bank else None),
                    "название банка": _safe(lessor_bank.bank_name if lessor_bank else None),
                    "BIC": _safe(lessor_bank.bic if lessor_bank else None, ""),
                    "SWIFT": _safe(lessor_bank.swift if lessor_bank else None, ""),
                }
                _replace_in_table(table, lessor_bank_repl)

        # TABLE 5: Final signatures (От имени Лизингодателя / Лизингополучателя)
        if cols == 2 and rows >= 6:
            first_c0 = table.rows[0].cells[0].text if table.rows[0].cells else ""
            first_c1 = table.rows[0].cells[1].text if len(table.rows[0].cells) > 1 else ""
            if "Лизингодателя" in first_c0 or "Лизингополучателя" in first_c1:
                _replace_in_table_column(table, 0, {
                    "Организационно правовая форма": _legal_form(lessor_user),
                    "Название компании": _user_name(lessor_user),
                    "ФИО директора": _director_or_name(lessor_user),
                })
                _replace_in_table_column(table, 1, {
                    "Организационно правовая форма": _legal_form(lessee_user) if lessee_user and lessee_user.company else ("ИП" if lessee_user and lessee_user.entrepreneur else ""),
                    "Название компании": _user_name(lessee_user),
                    "ФИО директора": _director_or_name(lessee_user),
                })

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _build_la_info_block(u) -> dict[str, str]:
    """Build replacements for the ИНФОРМАЦИЯ О ... blocks in the leasing agreement."""
    bank = _first_bank(u)
    return {
        "Организационно правовая форма": _legal_form(u),
        "Название компании": _user_name(u),
        "УНП": _unp(u),
        "юридический адрес": _legal_address(u),
        "почтовый адрес": _postal_address(u),
        "номера телефонов": _contact_phone(u),
        "электронная почта": _contact_email(u),
        "IBAN": _safe(bank.iban if bank else None),
        "название банка": _safe(bank.bank_name if bank else None),
        "BIC": _safe(bank.bic if bank else None, ""),
        "SWIFT": _safe(bank.swift if bank else None, ""),
        "ФИО директора": _director_or_name(u),
        "ФИО": _director_or_name(u),
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_contract_document(buf: BytesIO, folder: str, filename: str) -> str:
    """Upload a DOCX buffer to MinIO and return the public URL."""
    object_name = f"{folder}/{filename}"
    data = buf.read()
    storage_service.client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        BytesIO(data),
        length=len(data),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    return f"http://{settings.MINIO_EXTERNAL_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
