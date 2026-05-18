import requests
import json
import csv

# Config
url = "http://localhost:8019" #your odoo url
username = "admin" #your username
password = "admin" # your password
dbname = "odoo19" #your db name

json_rpc_endpoint = f"{url}/jsonrpc"

# Generic JSON-RPC caller
def json_rpc_call(service, method, args):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args,
        },
        "id": 1,
    }
    response = requests.post(json_rpc_endpoint, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()
    if 'error' in result:
        raise Exception(result['error'])
    return result['result']

# Login
uid = json_rpc_call("common", "login", [dbname, username, password])
print(f"✅ Logged in as UID: {uid}")


def create_contact(vals):
    """Create a partner and return its ID."""
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'create', [vals]])

def read_contacts(ids, fields=None):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'read', [ids], {'fields': fields or ['name', 'phone', 'email', 'city']}])

def update_contact(pid, vals):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'write', [[pid], vals]])

def delete_contact(pid):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'unlink', [[pid]]])

def search_contacts(domain=None, fields=None):
    ids = json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'search', [domain or []]])
    return read_contacts(ids, fields=fields)

def get_category_ids(names):
    """Return a list of category (tag) IDs matching the given names."""
    result = []
    for name in names:
        ids = json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner.category', 'search', [[('name', '=', name)]], {'limit': 1}])
        if ids:
            result.append(ids[0])
    return result


def create_contact_cli():
    """Interactive prompt."""
    ctype = input("Contact Type ('individual' / 'company'): ").strip().lower()

    if ctype == "company":
        vals = {
            'is_company': True,
            'name': input("Company name: "),
            'street': input("Street: "),
            'street2': input("Street 2 (optional): "),
            'city': input("City: "),
            'state_id': False,
            'zip': input("ZIP/Postcode: "),
            'country_id': False,
            'phone': input("Phone: "),
            'mobile': input("Mobile (optional): "),
            'email': input("Email: "),
            'website': input("Website URL: "),
            'vat': input("Tax ID / VAT: "),
            'category_id': [(6, 0, get_category_ids(['Company']))],
        }

    elif ctype == "individual":
        vals = {
            'is_company': False,
            'name': input("Full name: "),
            'function': input("Job position (e.g. Sales Director): "),
            'street': input("Street: "),
            'street2': input("Street 2 (optional): "),
            'city': input("City: "),
            'state_id': False,
            'zip': input("ZIP/Postcode: "),
            'country_id': False,
            'phone': input("Phone: "),
            'mobile': input("Mobile (optional): "),
            'email': input("Email: "),
            'website': input("Website URL (optional): "),
            'vat': input("Tax ID / VAT (optional): "),
            'category_id': [(6, 0, get_category_ids(['Artist', 'Media']))],
        }

    else:
        print("Invalid choice. Type 'individual' or 'company'.")
        return

    pid = create_contact(vals)
    print(f"\n Contact created with ID: {pid}")

def view_contacts_cli():
    contacts = search_contacts(fields=['id', 'name', 'phone', 'email', 'city'])
    if not contacts:
        print("No contacts found.")
        return
    print("\n=== Contacts ===")
    for c in contacts:
        print(f"{c['id']:>4} | {c['name']:<30} | {c.get('phone','-'):<15} | {c.get('email','-'):<25} | {c.get('city','-')}")

def update_contact_cli():
    pid = int(input("ID to update: "))
    field = input("Field to update (e.g. city, phone, email): ")
    value = input(f"New value for {field}: ")
    ok = update_contact(pid, {field: value})
    print(" Updated." if ok else " Update failed.")

def delete_contact_cli():
    pid = int(input("ID to delete: "))
    ok = delete_contact(pid)
    print(" Deleted." if ok else " Delete failed.")

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
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(contacts, f, indent=4)
    print(f" Exported to JSON: {filename}")


def main():
    MENU = {
        "1": ("Create contact", create_contact_cli),
        "2": ("View contacts", view_contacts_cli),
        "3": ("Update contact", update_contact_cli),
        "4": ("Delete contact", delete_contact_cli),
        "5": ("Export contacts to CSV", export_contacts_to_csv),
        "6": ("Export contacts to JSON", export_contacts_to_json),
        "7": ("Exit", None),
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
