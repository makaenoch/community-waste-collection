# Community Waste Collection Management

A MongoDB NoSQL coursework project with a browser interface for registering households, assigning waste collectors, tracking pickup requests and recording service payments.

## Technologies

Python 3.10+, MongoDB Community Server, PyMongo, HTML, CSS and JavaScript. MongoDB Compass is optional for inspecting documents. Flask and Gunicorn support the optional cloud deployment.

## Run locally

1. Install Python 3.10+ and MongoDB Community Server. Start MongoDB on localhost:27017.
2. Download this repository using **Code → Download ZIP** and extract it.
3. Open a terminal in the extracted project folder.
4. Install the local dependency:

```sh
python -m pip install pymongo==4.15.4
```

5. If you do not already have the coursework database, load the fictional sample:

```sh
python seed_database.py
```

The importer refuses to run if any project collection already contains records. Existing users should skip this step. An interrupted import is not automatically rolled back; inspect its results before retrying.

6. Start the application:

```sh
python app.py
```

7. Open http://127.0.0.1:8765 and keep the terminal open. On Windows, use `py` instead of `python` if needed.

## Database design

Database: `enoch_1012_community_waste_midsem`.

| Collection | Purpose |
| --- | --- |
| households | Profiles with embedded zone and landmark |
| collectors | Workers with an array of service areas |
| collection_requests | Pickup jobs referencing household and collector IDs |
| payments | Billing records referencing request and household IDs |

The sample contains five documents in each collection, twenty total. It uses fictional records, string identifiers, BSON dates and whole Uganda shillings. Its original results are two pending pickups and UGX 25,000 paid revenue. Testing payments can change these totals.

## CRUD features

- **Create:** register households and collectors, submit pickups and create bills.
- **Read:** view and search all four collections; inspect dashboard totals.
- **Update:** edit records through prefilled forms; schedule or complete pickups and mark charges paid.
- **Delete:** delete records after confirmation. Linked parent records cannot be deleted until dependent records are removed.

The backend checks positive amounts and bag counts, service areas, active collectors and valid linked IDs. A unique payment request index prevents duplicate billing. IDs and request creation dates stay fixed during edits. See CRUD_DEMONSTRATION.md for the classroom walkthrough.

## Limits and verification

Local mode binds to this computer only and has no login. It does not process money. Application-level relationship checks do not replace database foreign keys or transactions, and concurrent external edits can violate them. Use this as a coursework prototype.

Python and JavaScript syntax and simulated CRUD checks passed during development. The original local application was demonstrated against MongoDB. The latest edit/delete revision still requires a live end-to-end check on the presenter’s computer.

## Optional online deployment

See ONLINE_SETUP.md for Atlas and Render. Install requirements.txt for that deployment. Configure MONGODB_URI and APP_PASSWORD as hosting secrets; never commit them. Cloud mode uses a shared demonstration login. GitHub stores the source; GitHub Pages cannot run this Python backend.
