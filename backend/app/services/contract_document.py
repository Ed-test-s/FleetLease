"""Generate DOCX contracts from Word templates by replacing [placeholder] markers."""

import copy
import os
import re
import uuid
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from app.core.config import settings
from app.services.storage import storage_service

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "contracts_examples"
PSA_TEMPLATE = TEMPLATES_DIR / "шаблон_договор_купли_продажи.docx"
LA_TEMPLATE = TEMPLATES_DIR / "шаблон_договор_лизинга.docx"


def _num_to_words(n: float) -> str:
    """Rough Russian number-to-words for contract sums (simplified)."""
    n = round(n, 2)
    int_part = int(n)
    frac = round((n - int_part) * 100)

    if int_part == 0:
        return f"ноль руб. {frac:02d} коп."

    groups = []
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
        parts = []
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

    result_parts = []
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
    return f"{text} руб. {frac:02d} коп."


def _replace_in_paragraph(paragraph, replacements: dict[str, str]) -> None:
    """Replace [placeholder] patterns even when they span multiple runs."""
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

    first_run = paragraph.runs[0]
    style = first_run.style
    font_name = first_run.font.name
    font_size = first_run.font.size
    bold = first_run.font.bold
    italic = first_run.font.italic

    for run in paragraph.runs:
        run.text = ""
    paragraph.runs[0].text = new_text


def _replace_in_table(table, replacements: dict[str, str]) -> None:
    for row in table.rows:
        for cell in row.cells:
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


def _safe(val, default="___________") -> str:
    if val is None or val == "":
        return default
    return str(val)


def build_psa_replacements(
    contract,
    vehicle,
    supplier_user,
    lessor_user,
    lessee_user,
) -> dict[str, str]:
    """Build placeholder->value map for the purchase-sale agreement template."""
    from datetime import timedelta

    supplier_company = supplier_user.company if supplier_user else None
    lessor_company = lessor_user.company if lessor_user else None
    lessee_company = lessee_user.company if lessee_user else None if lessee_user else None
    lessee_individual = lessee_user.individual if lessee_user else None

    price = vehicle.price if vehicle else 0
    quantity = contract.quantity or 1
    total_price = price * quantity
    vat_rate = contract.vat_rate or 20
    vat_amount = round(total_price * vat_rate / (100 + vat_rate), 2)
    price_without_vat = round(total_price - vat_amount, 2)
    half_price = round(total_price / 2, 2)

    condition = "новый" if vehicle and vehicle.condition == "new" else "б/у"
    condition_full_new = "Товар является новым. В связи с этим Продавец предоставляет гарантию на передаваемый товар согласно условиям."
    condition_full_used = "Товар является бывшим в эксплуатации и передается Покупателю в том состоянии, в котором он фактически находится на момент его передачи. В связи с этим Продавец не предоставляет гарантию на передаваемый товар, обмену и возврату товар не подлежит."
    condition_full = condition_full_new if condition == "новый" else condition_full_used

    warranty_new = "Продавец несет ответственность за скрытые недостатки товара."
    warranty_used = "Продавец не несет ответственности за скрытые недостатки товара в связи с тем, что товар является бывшим в эксплуатации."
    warranty_text = warranty_new if condition == "новый" else warranty_used

    three_days = (contract.signing_date + timedelta(days=3)) if contract.signing_date else None

    supplier_bank = supplier_user.bank_accounts[0] if supplier_user and supplier_user.bank_accounts else None
    supplier_contact_phone = next((c.value for c in (supplier_user.contacts if supplier_user else []) if c.type.value == "phone"), "")
    supplier_contact_email = next((c.value for c in (supplier_user.contacts if supplier_user else []) if c.type.value == "email"), "")

    def _user_name(u):
        if u and u.company:
            return u.company.company_name or ""
        if u and u.individual:
            return u.individual.full_name or ""
        if u and u.entrepreneur:
            return u.entrepreneur.full_name or ""
        return ""

    def _legal_form(u):
        if u and u.company:
            return u.company.legal_form or ""
        return ""

    def _legal_form_and_name(u):
        lf = _legal_form(u)
        name = _user_name(u)
        if lf:
            return f'{lf} "{name}"'
        return name

    def _director(u):
        if u and u.company:
            return u.company.director_name or ""
        if u and u.individual:
            return u.individual.full_name or ""
        return ""

    def _unp(u):
        if u and u.company:
            return u.company.unp or ""
        if u and u.entrepreneur:
            return u.entrepreneur.unp or ""
        return ""

    def _legal_address(u):
        if u and u.company:
            return u.company.legal_address or ""
        if u and u.entrepreneur:
            return u.entrepreneur.legal_address or ""
        return ""

    return {
        "номер ДКП": _safe(contract.contract_number),
        "год подписания": str(contract.signing_date.year) if contract.signing_date else "____",
        "город подписания": _safe(contract.signing_city),
        "дата подписания": _format_date(contract.signing_date),
        "валюта": _safe(contract.currency, "BYN"),
        "число НДС": str(vat_rate),
        "число НДС на момент подписания": str(vat_rate),
        "сумма НДС": f"{vat_amount:.2f}",
        "сумма НДС словами": _num_to_words(vat_amount),
        "кол-во": str(quantity),
        "тип ТС": _safe(vehicle.vehicle_type if vehicle else None, "транспортное средство"),
        "наименование полностью": _safe(vehicle.name if vehicle else None),
        "год выпуска": _safe(vehicle.release_year if vehicle else None),
        "VIN-номер": _safe(vehicle.vin if vehicle else None),
        "№техпаспорта": _safe(contract.tech_passport_number),
        "дата выдачи": _format_date(contract.tech_passport_date),
        "состояние": condition,
        "состояние товара полностью": condition_full,
        "цена в объявлении": f"{total_price:.2f}",
        "цена из объявления словами": _num_to_words(total_price),
        "цена в объявлении – сумма НДС": f"{price_without_vat:.2f}",
        "сумма словами": _num_to_words(total_price),
        "половина от полной цены в объявлении": f"{half_price:.2f}",
        "половина от полной цены словами": _num_to_words(half_price),
        "способ оплаты": "безналичный расчет",
        "дата, спустя три дня со дня формирования договора": _format_date(three_days),

        "Название компании": _user_name(supplier_user),
        "название компании": _user_name(supplier_user),
        "Организационно-правовая форма": _legal_form(supplier_user),
        "организ-прав. форма": _legal_form(supplier_user),
        "Организационно-правовая форма и Название компании": _legal_form_and_name(supplier_user),
        "ФИО директора": _director(supplier_user),
        "ФИО директора поставщика": _director(supplier_user),
        "ФИО директора продавца": _director(supplier_user),
        "УНП": _unp(supplier_user),
        "юридический адрес": _legal_address(supplier_user),
        "юридический адрес поставщика": _legal_address(supplier_user),
        "номер телефона": supplier_contact_phone,
        "электронная почта": supplier_contact_email,
        "название банка": _safe(supplier_bank.bank_name if supplier_bank else None),
        "IBAN": _safe(supplier_bank.iban if supplier_bank else None),
        "SWIFT": _safe(supplier_bank.swift if supplier_bank else None),

        "ФИО директора лизингодателя": _director(lessor_user),
        "юридический адрес поставщика": _legal_address(supplier_user),

        "ФИО директора лизингополучателя": _director(lessee_user) if lessee_user else "",
        "юридический адрес лизингополучателя": _legal_address(lessee_user) if lessee_user else "",

        "половина от полной цены словами": _num_to_words(half_price),
        "Продавец не несет ответственности за скрытые недостатки товара в связи с тем, что товар является бывшим в эксплуатации. ИЛИ: Продавец несет ответственность за скрытые недостатки товара.": warranty_text,
        "Товар является бывшим в эксплуатации и передается Покупателю в том состоянии, в котором он фактически находится на момент его передачи. В связи с этим Продавец не предоставляет гарантию на передаваемый товар, обмену и возврату товар не подлежит. ИЛИ: Товар является новым. В связи с этим Продавец предоставляет гарантию на передаваемый товар согласно условиям.": condition_full,

        "номер ДКП": _safe(contract.contract_number),
        "номер телефона": supplier_contact_phone,
    }


def build_la_replacements(
    contract,
    vehicle,
    lessor_user,
    lessee_user,
) -> dict[str, str]:
    """Build placeholder->value map for the leasing agreement template."""
    lessor_company = lessor_user.company if lessor_user else None
    lessee_company = lessee_user.company if lessee_user else None
    lessee_individual = lessee_user.individual if lessee_user else None

    price = vehicle.price if vehicle else 0
    total = contract.total_amount or 0
    vat_rate = contract.vat_rate or 20
    vat_on_total = round(total * vat_rate / (100 + vat_rate), 2)
    price_without_vat = round(price - (price * vat_rate / (100 + vat_rate)), 2)
    vat_on_price = round(price * vat_rate / (100 + vat_rate), 2)

    def _user_name(u):
        if u and u.company:
            return u.company.company_name or ""
        if u and u.individual:
            return u.individual.full_name or ""
        if u and u.entrepreneur:
            return u.entrepreneur.full_name or ""
        return ""

    def _legal_form(u):
        if u and u.company:
            return u.company.legal_form or ""
        return ""

    def _director(u):
        if u and u.company:
            return u.company.director_name or ""
        if u and u.individual:
            return u.individual.full_name or ""
        return ""

    def _unp(u):
        if u and u.company:
            return u.company.unp or ""
        if u and u.entrepreneur:
            return u.entrepreneur.unp or ""
        return ""

    def _legal_address(u):
        if u and u.company:
            return u.company.legal_address or ""
        if u and u.entrepreneur:
            return u.entrepreneur.legal_address or ""
        return ""

    lessor_bank = lessor_user.bank_accounts[0] if lessor_user and lessor_user.bank_accounts else None

    return {
        "номер договора лизинга": _safe(contract.contract_number),
        "номер-договора": _safe(contract.contract_number),
        "город подписания": _safe(contract.signing_city),
        "дата подписания": _format_date(contract.signing_date),
        "дата окончания срока": _format_date(contract.end_date),
        "валюта": _safe(contract.currency, "BYN"),
        "текущий НДС": str(contract.vat_rate or vat_rate),
        "число НДС на момент подписания": str(contract.vat_rate or vat_rate),
        "кол-во": str(contract.quantity or 1),
        "тип ТС": _safe(vehicle.vehicle_type if vehicle else None, "транспортное средство"),
        "название полностью": _safe(vehicle.name if vehicle else None),
        "год выпуска": _safe(vehicle.release_year if vehicle else None),
        "VIN номер": _safe(vehicle.vin if vehicle else None),
        "состояние": "новый" if vehicle and vehicle.condition == "new" else "б/у",

        "цена в объявлении": f"{price:.2f}",
        "цена в объявлении – сумма НДС": f"{price_without_vat:.2f}",
        "сумма НДС": f"{vat_on_price:.2f}",
        "сумма договора лизинга": f"{total:.2f}",
        "число": f"{total:.2f}",
        "число словами": _num_to_words(total),
        "число суммы договора лизинга словами": _num_to_words(total),
        "сумма НДС от договора лизинга": f"{vat_on_total:.2f}",
        "сумма НДС от договора лизинга словами": _num_to_words(vat_on_total),
        "номер договора лизинга": _safe(contract.contract_number),
        "сумма договора лизинга": f"{total:.2f}",
        "номер-договора": _safe(contract.contract_number),

        "Название компании": _user_name(lessor_user),
        "Название компании лизингодателя": _user_name(lessor_user),
        "Организационно правовая форма": _legal_form(lessor_user),
        "ФИО директора": _director(lessor_user),
        "ФИО": _director(lessee_user) if lessee_user else "",
        "УНП": _unp(lessor_user),
        "юридический адрес лизингодателя": _legal_address(lessor_user),
        "юридический адрес лизингополучателя": _legal_address(lessee_user) if lessee_user else "",

        "название банка": _safe(lessor_bank.bank_name if lessor_bank else None),
        "IBAN": _safe(lessor_bank.iban if lessor_bank else None),
        "BIC": _safe(lessor_bank.swift or (lessor_bank.bic if lessor_bank else None)),

        "Название компании лизингодателя": _user_name(lessor_user),
        "номер договора лизинга": _safe(contract.contract_number),
        "номер-договора": _safe(contract.contract_number),

        "сумма НДС от договора лизинга": f"{vat_on_total:.2f}",
        "сумма НДС от договора лизинга словами": _num_to_words(vat_on_total),
        "номер договора лизинга": _safe(contract.contract_number),

        "текущий НДС": str(contract.vat_rate or vat_rate),
        "число НДС на момент подписания": str(contract.vat_rate or vat_rate),

        "Название компании": _user_name(lessor_user),
        "Название компании лизингодателя": _user_name(lessor_user),

        "номер договора лизинга": _safe(contract.contract_number),
    }


def generate_psa_document(contract, vehicle, supplier_user, lessor_user, lessee_user) -> BytesIO:
    doc = Document(str(PSA_TEMPLATE))
    replacements = build_psa_replacements(contract, vehicle, supplier_user, lessor_user, lessee_user)
    _replace_in_doc(doc, replacements)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def generate_la_document(contract, vehicle, lessor_user, lessee_user) -> BytesIO:
    doc = Document(str(LA_TEMPLATE))
    replacements = build_la_replacements(contract, vehicle, lessor_user, lessee_user)
    _replace_in_doc(doc, replacements)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def upload_contract_document(buf: BytesIO, folder: str, filename: str) -> str:
    """Upload a DOCX buffer to MinIO and return the public URL."""
    object_name = f"{folder}/{filename}"
    data = buf.read()
    from io import BytesIO as _BytesIO
    storage_service.client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        _BytesIO(data),
        length=len(data),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    return f"http://{settings.MINIO_EXTERNAL_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
