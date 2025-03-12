# Standard schema for invoice data extraction

INVOICE_SCHEMA = {
    "invoice_number": "The unique identifier for this invoice",
    "invoice_date": "The date when the invoice was issued (YYYY-MM-DD format)",
    "due_date": "The date when payment is due (YYYY-MM-DD format)",
    "vendor": {
        "name": "The name of the vendor/supplier",
        "address": "The full address of the vendor",
        "phone": "The phone number of the vendor",
        "email": "The email address of the vendor",
        "tax_id": "The tax ID or business registration number of the vendor"
    },
    "customer": {
        "name": "The name of the customer/client",
        "address": "The full address of the customer",
        "phone": "The phone number of the customer",
        "email": "The email address of the customer"
    },
    "items": [
        {
            "description": "Description of the product or service",
            "quantity": "The quantity of the item",
            "unit_price": "The price per unit",
            "total_price": "The total price for this item (quantity × unit_price)"
        }
    ],
    "subtotal": "The sum of all item totals before tax and discounts",
    "tax": "The tax amount",
    "discount": "Any discount applied",
    "shipping": "Shipping or delivery charges",
    "total_amount": "The final total amount to be paid",
    "payment_terms": "The terms of payment",
    "payment_method": "The method of payment",
    "notes": "Any additional notes or comments on the invoice"
}
