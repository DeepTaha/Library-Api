from pathlib import Path
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _fmt(dt: datetime | None) -> str:
    """Format a timezone-aware datetime to a readable string, or return '—'."""
    if dt is None:
        return "—"
    return dt.astimezone().strftime("%d %b %Y, %I:%M %p")


def generate_borrowing_report_pdf(user, borrowings: list) -> bytes:
    """
    Render the borrowing_report.html template for `user` and their `borrowings`,
    then convert to PDF bytes via WeasyPrint.

    Each item in `borrowings` must be a Borrowing ORM object with .book loaded.
    """
    borrowing_rows = []
    active = overdue = returned = 0

    for b in borrowings:
        if b.returned_at:
            returned += 1
        elif b.is_overdue:
            overdue += 1
        else:
            active += 1

        borrowing_rows.append({
            "book_title":     b.book.title,
            "book_author":    b.book.author,
            "book_genre":     b.book.genre,
            "borrowed_at":    _fmt(b.borrowed_at),
            "due_date":       _fmt(b.due_date),
            "returned_at":    _fmt(b.returned_at),
            "extension_count": b.extension_count,
            "is_overdue":     b.is_overdue,
        })

    context = {
        "username":     user.username,
        "email":        user.email,
        "role":         user.role.value,
        "created_at":   _fmt(user.created_at),
        "is_suspended": user.is_suspended,
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC"),
        "borrowings":   borrowing_rows,
        "total":        len(borrowings),
        "active":       active,
        "overdue":      overdue,
        "returned":     returned,
    }

    template = _jinja_env.get_template("borrowing_report.html")
    html_string = template.render(**context)

    pdf_bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes
