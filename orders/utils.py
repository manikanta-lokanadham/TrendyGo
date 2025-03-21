from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from decimal import Decimal

def generate_invoice_pdf(order):
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'
    
    # Create a buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add company logo if exists
    # if settings.COMPANY_LOGO:
    #     img = Image(settings.COMPANY_LOGO)
    #     img.drawHeight = 1*inch
    #     img.drawWidth = 2*inch
    #     elements.append(img)
    #     elements.append(Spacer(1, 12))
    
    # Add invoice title
    elements.append(Paragraph(f"Invoice #{order.order_id}", title_style))
    elements.append(Spacer(1, 12))
    
    # Add order date
    elements.append(Paragraph(f"Date: {order.created_at.strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Add customer information
    elements.append(Paragraph("Customer Information", heading_style))
    elements.append(Spacer(1, 6))
    
    customer_info = [
        f"Name: {order.first_name} {order.last_name}",
        f"Email: {order.email}",
        f"Phone: {order.phone}",
    ]
    
    # Add shipping address if available
    shipping_address = getattr(order, 'shipping_address', None)
    if shipping_address:
        customer_info.append(f"Address: {shipping_address}")
    
    for info in customer_info:
        elements.append(Paragraph(info, normal_style))
    elements.append(Spacer(1, 12))
    
    # Add order items
    elements.append(Paragraph("Order Items", heading_style))
    elements.append(Spacer(1, 6))
    
    # Create the table data
    table_data = [['Item', 'Quantity', 'Price', 'Total']]
    
    # Calculate subtotal from order items
    items_subtotal = Decimal('0.00')
    for item in order.items.all():
        item_total = item.price * item.quantity
        items_subtotal += item_total
        table_data.append([
            item.product.name,
            str(item.quantity),
            f"${item.price:.2f}",
            f"${item_total:.2f}"
        ])
    
    # Calculate or use existing values
    # Check for attribute existence
    subtotal = getattr(order, 'subtotal', None) or items_subtotal
    shipping_cost = getattr(order, 'shipping_cost', None) or Decimal('0.00')
    tax = getattr(order, 'tax', None) or (subtotal * Decimal('0.10'))  # 10% tax if not specified
    discount = getattr(order, 'discount', None) or Decimal('0.00')
    
    # Calculate final total
    total = getattr(order, 'total', None)
    if total is None:
        total = subtotal + shipping_cost + tax - discount
    
    # Add summary rows
    table_data.extend([
        ['', '', 'Subtotal:', f"${subtotal:.2f}"],
        ['', '', 'Shipping:', f"${shipping_cost:.2f}"],
        ['', '', 'Tax:', f"${tax:.2f}"],
        ['', '', 'Discount:', f"${discount:.2f}"],
        ['', '', 'Total:', f"${total:.2f}"]
    ])
    
    # Create the table
    table = Table(table_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -5), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -5), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -5), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -5), (-1, -1), 12),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),  # Highlight total row
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Add payment information
    elements.append(Paragraph("Payment Information", heading_style))
    elements.append(Spacer(1, 6))
    
    # Use safe attribute access
    payment_method = getattr(order, 'payment_method', None)
    payment_status = getattr(order, 'payment_status', None)
    transaction_id = getattr(order, 'transaction_id', None)
    
    payment_info = []
    
    if hasattr(order, 'get_payment_method_display') and callable(getattr(order, 'get_payment_method_display')):
        payment_info.append(f"Payment Method: {order.get_payment_method_display() or 'N/A'}")
    elif payment_method:
        payment_info.append(f"Payment Method: {payment_method}")
    else:
        payment_info.append("Payment Method: N/A")
    
    if hasattr(order, 'get_payment_status_display') and callable(getattr(order, 'get_payment_status_display')):
        payment_info.append(f"Payment Status: {order.get_payment_status_display() or 'N/A'}")
    elif payment_status:
        payment_info.append(f"Payment Status: {payment_status}")
    else:
        payment_info.append("Payment Status: N/A")
    
    if transaction_id:
        payment_info.append(f"Transaction ID: {transaction_id}")
    
    for info in payment_info:
        elements.append(Paragraph(info, normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response
