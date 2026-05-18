To Run:

1.Fastapi_crud.py
2.jsonrpc_crud.py
3.xmlrpc_crud.py

Step 1:

Install the requirements
    fastapi
    uvicorn
    requests
    pydantic

Step 2:

First edit each program's  

url = "http://localhost:8020" #your odoo url
username = "admin" #your username
password = "admin" # your password
dbname = "test17" #your db name

According to your odoo instance


And run your odoo instance.
Then run each program seperately in your machine.

Step 3:
 
Command to run each program:

uvicorn Fastapi_crud:app --reload
then paste the below url in browser
http://127.0.0.1:8000/docs

python jsonrpc_crud.py
python xmalrpc_crud.py

**************************************************************************************************


