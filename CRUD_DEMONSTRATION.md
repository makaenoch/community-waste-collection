# Lecturer demonstration

## Load the updated application

Close the old command window or press Ctrl+C in it. Double-click Start Application.cmd again and refresh http://127.0.0.1:8765. Every section now has Edit and Delete buttons in the Manage column. On narrow screens, scroll the table horizontally to see these buttons.

## Demonstrate all four CRUD operations

Use new practice records so the original report records stay intact.

1. In Households, create a household named Lecturer Demo Household in Kawempe, with a zone, landmark and pickup day. This demonstrates Create. The saved row demonstrates Read.
2. Click Edit, change the landmark and save. Refresh Compass's households collection to show the update was stored in MongoDB.
3. Register Lecturer Demo Collector with service area Kawempe and vehicle code DEMO-CLASS. Edit the vehicle code to demonstrate collector editing.
4. Create a pickup for that household and collector. Edit its waste type or bag count, then use Schedule and Complete pickup. The Edit form can also correct its status.
5. Create a billing record for that request as unpaid. Edit the amount, then use Mark paid. The dashboard totals update. This records payment information only; no money is transferred.
6. Try deleting the household while its request exists. The application should explain that linked records must be removed first.
7. Delete the demonstration billing record, then its pickup request, then its household and collector. Confirm each deletion. Refresh Compass to show the records were removed.

Do not delete the original H001–H005, C001–C005, R001–R005 or P001–P005 records during this demonstration.

The system supports Create, Read, Update and Delete across all four collections. Application-level link checks assume records are edited through this single application instance, rather than changed concurrently in Compass or another application.
