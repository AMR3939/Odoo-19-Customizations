from xmlrpc import client as xmlrpclib
import csv
import json
# Config

url       = "http://localhost:8019" #your odoo url
username  = "admin" #your username
password  = "admin" #your password
dbname    = "odoo19" #your dbname

# XML‑RPC end‑points
common = xmlrpclib.ServerProxy(f"{url}/xmlrpc/2/common")
uid     = common.login(dbname, username, password)
models  = xmlrpclib.ServerProxy(f"{url}/xmlrpc/2/object")

print(f"Logged in as UID: {uid}")



def create_contact(vals: dict) -> int:
    """Create a partner and return its ID."""
    return models.execute_kw(
        dbname, uid, password,
        'res.partner', 'create',
        [vals]
    )

def read_contacts(ids, fields=None):
    return models.execute_kw(
        dbname, uid, password,
        'res.partner', 'read',
        [ids],
        {'fields': fields or ['name', 'phone', 'email', 'city']}
    )

def update_contact(pid: int, vals: dict):
    return models.execute_kw(
        dbname, uid, password,
        'res.partner', 'write',
        [[pid], vals]
    )

def delete_contact(pid: int):
    return models.execute_kw(
        dbname, uid, password,
        'res.partner', 'unlink',
        [[pid]]
    )

def search_contacts(domain=None, fields=None):
    ids = models.execute_kw(
        dbname, uid, password,
        'res.partner', 'search',
        [domain or []]
    )
    return read_contacts(ids, fields=fields)

def get_category_ids(names):
    """Return a list of category (tag) IDs matching the given names."""
    result = []
    for name in names:
        ids = models.execute_kw(
            dbname, uid, password,
            'res.partner.category', 'search',
            [[('name', '=', name)]], {'limit': 1}
        )
        if ids:
            result.append(ids[0])
    return result


def create_contact_cli():
    """Interactive prompt that matches the form fields in the screenshots."""
    ctype = input("Contact Type ('individual' / 'company'): ").strip().lower()

    if ctype == "company":
        vals = {
            'is_company': True,
            'name'      : input("Company name: "),
            'street'    : input("Street: "),
            'street2'   : input("Street 2 (optional): "),
            'city'      : input("City: "),
            'state_id'  : False,
            'zip'       : input("ZIP/Postcode: "),
            'country_id': False,   # idem
            'phone'     : input("Phone: "),
            'mobile'    : input("Mobile (optional): "),
            'email'     : input("Email: "),
            'website'   : input("Website URL: "),
            'vat'       : input("Tax ID / VAT: "),
            'category_id': [(6, 0, get_category_ids(['Company']))],
        }

    elif ctype == "individual":
        vals = {
            'is_company': False,
            'name'      : input("Full name: "),
            'function' : input("Job position (e.g. Sales Director): "),
            'street'    : input("Street: "),
            'street2'   : input("Street 2 (optional): "),
            'city'      : input("City: "),
            'state_id'  : False,
            'zip'       : input("ZIP/Postcode: "),
            'country_id': False,
            'phone'     : input("Phone: "),
            'mobile'    : input("Mobile (optional): "),
            'email'     : input("Email: "),
            'website'   : input("Website URL (optional): "),
            'vat'       : input("Tax ID / VAT (optional): "),
            'category_id': [(6, 0, get_category_ids(['Artist', 'Media']))],
        }

    else:
        print(" Invalid choice. Type 'individual' or 'company'.")
        return

    pid = create_contact(vals)
    print(f"\n  Contact created with ID: {pid}")

def view_contacts_cli():
    contacts = search_contacts(fields=['id','name','phone','email','city'])
    if not contacts:
        print("No contacts found.")
        return
    print("\n=== Contacts ===")
    for c in contacts:
        print(f"{c['id']:>4} | {c['name']:<30} | "
              f"{c.get('phone','-'):<15} | {c.get('email','-'):<25} | {c.get('city','-')}")

def update_contact_cli():
    pid = int(input("ID to update: "))
    field = input("Field to update (e.g. city, phone, email): ")
    value = input(f"New value for {field}: ")
    ok = update_contact(pid, {field: value})
    print("Updated." if ok else "Update failed.")


def delete_contact_cli():
    pid = int(input("ID to delete: "))
    ok = delete_contact(pid)
    print("Deleted." if ok else "Delete failed.")

def export_contacts_to_csv(filename="contacts_export.csv"):
    contacts = search_contacts(fields=['id', 'name', 'phone', 'email', 'city'])
    if not contacts:
        print("No contacts to export.")
        return
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=contacts[0].keys())
        writer.writeheader()
        writer.writerows(contacts)
    print(f" Exported to CSV: {filename}")


def export_contacts_to_json(filename="contacts_export.json"):
    contacts = search_contacts(fields=['id', 'name', 'phone', 'email', 'city'])
    if not contacts:
        print("No contacts to export.")
        return
    with open(filename, "w") as f:
        json.dump(contacts, f, indent=4)
    print(f"Exported to JSON: {filename}")


def main():
    MENU = {
        "1": ("Create contact",   create_contact_cli),
        "2": ("View contacts",    view_contacts_cli),
        "3": ("Update contact",   update_contact_cli),
        "4": ("Delete contact",   delete_contact_cli),
        "5": ("Export contacts to CSV", export_contacts_to_csv),
        "6": ("Export contacts to JSON", export_contacts_to_json),
        "7": ("Exit",             None),
    }

    while True:
        print("\n===== Odoo Contact Manager =====")
        for k, (label, _) in MENU.items():
            print(f"{k}. {label}")
        choice = input("Choice: ").strip()

        action = MENU.get(choice, (None, None))[1]
        if action:
            action()
        elif choice == "7":
            print("Good‑bye!")
            break
        else:
            print(" Invalid selection.")

if __name__ == "__main__":
    main()
