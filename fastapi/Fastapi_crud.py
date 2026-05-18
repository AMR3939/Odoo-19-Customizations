from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import requests


import json
import csv
import os

# Config
url = "http://localhost:8019" #your odoo instance url
username = "admin" #your username
password = "admin" #your password
dbname = "odoo19" #your dbname
json_rpc_endpoint = f"{url}/jsonrpc"

#FastAPI App
app = FastAPI(title="Odoo Contact Manager")


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

#Login
uid = json_rpc_call("common", "login", [dbname, username, password])

# Models
class ContactCreate(BaseModel):
    name: str
    is_company: bool
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    category: Optional[List[str]] = None

class ContactUpdate(BaseModel):
    field: str
    value: str

# Odoo Operations
def get_category_ids(names):
    result = []
    for name in names or []:
        ids = json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner.category', 'search', [[('name', '=', name)]], {'limit': 1}])
        if ids:
            result.append(ids[0])
    return result

def create_contact(vals):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'create', [vals]])

def read_contacts(ids, fields=None):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'read', [ids], {'fields': fields or ['name', 'phone', 'email', 'city']}])

def search_contacts(domain=None, fields=None):
    ids = json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'search', [domain or []]])
    return read_contacts(ids, fields=fields)

def update_contact(pid, vals):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'write', [[pid], vals]])

def delete_contact(pid):
    return json_rpc_call("object", "execute_kw", [dbname, uid, password, 'res.partner', 'unlink', [[pid]]])

# API Endpoints

@app.post("/contacts/")
def api_create_contact(contact: ContactCreate):
    vals = {
        'name': contact.name,
        'is_company': contact.is_company,
        'phone': contact.phone,
        'email': contact.email,
        'city': contact.city,
        'category_id': [(6, 0, get_category_ids(contact.category or []))]
    }
    pid = create_contact(vals)
    return {"message": "Contact created", "id": pid}

@app.get("/contacts/")
def api_get_contacts():
    contacts = search_contacts(fields=['id', 'name', 'phone', 'email', 'city', 'is_company'])
    return contacts

@app.put("/contacts/{contact_id}")
def api_update_contact(contact_id: int, update: ContactUpdate):
    success = update_contact(contact_id, {update.field: update.value})
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")
    return {"message": "Contact updated"}

@app.delete("/contacts/{contact_id}")
def api_delete_contact(contact_id: int):
    success = delete_contact(contact_id)
    if not success:
        raise HTTPException(status_code=400, detail="Delete failed")
    return {"message": "Contact deleted"}

