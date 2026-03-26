from io import BytesIO

from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def build_simple_invoice_pdf(order):
    lines = [
        f"Invoice {order.order_number}",
        f"Customer: {order.full_name()}",
        f"Email: {order.email}",
        f"Status: {order.get_status_display()}",
        f"Total: {order.order_total}",
        "",
        "Items:",
    ]
    for item in order.items.select_related("product").all():
        lines.append(f"- {item.product.product_name} x {item.quantity} = {item.subtotal()}")

    content = "\\n".join(lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 780 Td ({content}) Tj ET"
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
        + f"4 0 obj<< /Length {len(stream)} >>stream\n{stream}\nendstream\nendobj\n".encode("latin-1")
        + b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        + b"xref\n0 6\n0000000000 65535 f \n"
        + b"0000000010 00000 n \n0000000062 00000 n \n0000000119 00000 n \n"
        + b"0000000247 00000 n \n0000000000 00000 n \n"
        + b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )
    return BytesIO(pdf)


def send_order_invoice(order):
    message = render_to_string("orders/invoice_email.txt", {"order": order})
    email = EmailMessage(
        subject=f"Your GreatKart receipt #{order.order_number}",
        body=message,
        to=[order.email],
    )
    email.attach(
        f"invoice-{order.order_number}.pdf",
        build_simple_invoice_pdf(order).getvalue(),
        "application/pdf",
    )
    email.send(fail_silently=True)
