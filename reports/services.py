from django.core.files.base import ContentFile
from django.utils import timezone

from finance.models import Expense, Income
from tax.services import calculate_tax_values

from .models import GeneratedReport


def generate_report(user, report_type):
    title, lines = _report_content(user, report_type)
    pdf_bytes = build_simple_pdf(lines)
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    filename = f"{report_type}-report-{user.pk}-{timestamp}.pdf"
    report = GeneratedReport.objects.create(
        user=user,
        report_type=report_type,
        title=title,
    )
    report.file.save(filename, ContentFile(pdf_bytes), save=True)
    return report


def _report_content(user, report_type):
    generated = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')
    header = [
        'ADARES CRM',
        f'User: {user.username}',
        f'Generated date: {generated}',
        '',
    ]

    if report_type == GeneratedReport.REPORT_INCOME:
        incomes = Income.objects.filter(user=user).select_related('source')
        total = sum((income.amount for income in incomes), 0)
        lines = header + [
            'Income report',
            f'Total income: R{total:.2f}',
            '',
            'Date | Source | Amount | Description',
        ]
        lines.extend(
            f'{income.date_received} | {income.source.name} | R{income.amount:.2f} | {income.description or "-"}'
            for income in incomes
        )
        return 'Income report', lines

    if report_type == GeneratedReport.REPORT_EXPENSE:
        expenses = Expense.objects.filter(user=user).select_related('category')
        total = sum((expense.amount for expense in expenses), 0)
        lines = header + [
            'Expense report',
            f'Total expenses: R{total:.2f}',
            '',
            'Date | Category | Amount | Description',
        ]
        lines.extend(
            f'{expense.date_paid} | {expense.category.name} | R{expense.amount:.2f} | {expense.description or "-"}'
            for expense in expenses
        )
        return 'Expense report', lines

    if report_type == GeneratedReport.REPORT_TAX:
        values = calculate_tax_values(user)
        lines = header + [
            'Tax summary report',
            f'Tax year: {values["tax_year"]}',
            f'Gross income: R{values["gross_income"]:.2f}',
            f'Deductible expenses: R{values["deductible_expenses"]:.2f}',
            f'Taxable income: R{values["taxable_income"]:.2f}',
            f'Bracket calculation: {values["bracket_description"]}',
            f'Tax before rebates: R{values["tax_before_rebates"]:.2f}',
            f'Rebate: R{values["rebate_amount"]:.2f}',
            f'Final estimated tax: R{values["estimated_tax"]:.2f}',
            '',
            'This is an estimate only and is not official tax advice.',
        ]
        return 'Tax summary report', lines

    raise ValueError('Unsupported report type')


def build_simple_pdf(lines):
    escaped_lines = [_escape_pdf_text(line) for line in lines]
    text_commands = ['BT', '/F1 12 Tf', '50 780 Td']
    for index, line in enumerate(escaped_lines):
        if index:
            text_commands.append('0 -18 Td')
        text_commands.append(f'({line}) Tj')
    text_commands.append('ET')
    stream = '\n'.join(text_commands).encode('latin-1', errors='replace')

    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length ' + str(len(stream)).encode('ascii') + b' >>\nstream\n' + stream + b'\nendstream',
    ]

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{number} 0 obj\n'.encode('ascii'))
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')
    xref_offset = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('ascii'))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode('ascii'))
    pdf.extend(
        f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n'.encode('ascii')
    )
    return bytes(pdf)


def _escape_pdf_text(value):
    return str(value).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
