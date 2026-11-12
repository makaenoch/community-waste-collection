# Publish the project for your lecturer

This package is prepared for Render with MongoDB Atlas. It is not yet deployed and has no public project URL. The local launcher continues to work as before. Cloud data is a separate copy; local and online changes do not automatically synchronize.

## 1 Create the online database

Sign in at https://cloud.mongodb.com/ and create an Atlas database deployment. Review the selected plan and any costs before creating it.

Create a database user with readWrite access limited to enoch_1012_community_waste_midsem. This is separate from your Atlas account. Keep its password private. Under Connect, choose Drivers and obtain the Python connection string. Enter the real database user and URL-encoded password when setting the hosting secret later. Do not put the connection string in GitHub or send it in chat.

## 2 Copy the current records

Run export_database.py with the same Python used by Start Application.cmd. It reads the local database without modifying it and writes four Extended JSON files in database-export.

Alternatively, export each of the four local collections in Compass using Extended JSON, retaining BSON dates.

Add your current computer IP to Atlas Network Access. Connect Compass to Atlas using the connection string. Create enoch_1012_community_waste_midsem with these collections: households, collectors, collection_requests, payments. Import the matching JSON into each empty collection once. Check all collection counts against the local database.

In Compass's shell connected to Atlas, run:

```javascript
db = db.getSiblingDB('enoch_1012_community_waste_midsem');
db.payments.createIndex({request_id:1},{unique:true});
db.collection_requests.createIndex({status:1,requested_at:1});
db.collection_requests.createIndex({household_id:1});
```

## 3 Upload the application source

Create a private GitHub repository and upload these files at the repository root: app.py, cloud.py, index.html, requirements.txt, render.yaml and .gitignore. Do not upload vendor, database-export, passwords, or connection strings.

## 4 Deploy on Render

Sign in at https://dashboard.render.com/ and connect the repository. Create a Web Service with Python runtime. Review the service plan and cost before creating it.

- Build command: pip install -r requirements.txt
- Start command: gunicorn cloud:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60
- Health check: /healthz
- MONGODB_URI: your Atlas connection string, saved as a secret
- WASTE_DATABASE: enoch_1012_community_waste_midsem
- APP_USERNAME: lecturer
- APP_PASSWORD: a new unique password of at least 16 characters, saved as a secret

Add the Render service's outbound IP ranges shown in its dashboard to the Atlas IP access list. Do not open Atlas to every internet address. Start or retry the deployment after adding those ranges.

## 5 Verify and share

Open the HTTPS onrender.com URL returned by Render. Verify that it asks for a username and password, rejects an incorrect password, and displays the imported records after a valid login. Test a new demonstration household and pickup instead of changing the original sample.

Share that exact HTTPS URL with the lecturer and provide the application username/password privately. Never share the Atlas password or connection string. This is a shared demonstration login: anyone given it can create records and change statuses. This prototype has no per-user roles or audit history.

Hosting readiness is not a verified deployment. Login, cloud connection and a full save-and-refresh flow must be tested after the accounts and secrets are configured.

Official references: https://render.com/docs/web-services and https://www.mongodb.com/docs/atlas/connect-to-database-deployment/
