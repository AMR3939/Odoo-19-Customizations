{
    "name": "Contact OCR Button",
    "version": "1.0",
    "author": "Your Name",
    "category": "Tools",
    "summary": "Add OCR scanning to contacts",
    "depends": ["base", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/ocr_label_view.xml",
        "views/res_partner_view.xml",
        "views/business_card_ocr_view.xml",


    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}