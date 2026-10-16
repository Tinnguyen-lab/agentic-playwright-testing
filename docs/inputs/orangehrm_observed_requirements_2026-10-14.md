# OrangeHRM Demo — observed functional requirements

Observation date: 2026-10-14

Target: https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
Test scope: read-only exploration of the public demo. Do not add, edit, or delete employee records.

## ORH-01 — Public-demo authentication

Actor: a public-demo user.

Precondition: the user opens the OrangeHRM login page. The page visibly publishes
the demo credentials `Admin` and `admin123`.

Main flow:

1. Enter `Admin` in the Username textbox.
2. Enter `admin123` in the Password textbox.
3. Select Login.

Expected outcome: the application opens the Dashboard at a URL ending in
`/web/index.php/dashboard/index`, and a Dashboard heading is visible.

## ORH-02 — Authenticated navigation menu

Actor: an authenticated public-demo user.

Precondition: the Dashboard is open.

Expected outcome: the sidepanel exposes the named navigation links `PIM`,
`Directory`, `Leave`, `Time`, `Recruitment`, `My Info`, `Performance`,
`Dashboard`, `Maintenance`, `Claim`, and `Buzz`.

## ORH-03 — PIM employee-list screen

Actor: an authenticated public-demo user.

Precondition: the Dashboard is open.

Main flow: select the PIM navigation link.

Expected outcome: the URL ends in `/web/index.php/pim/viewEmployeeList`. The page
shows heading `Employee Information`, filter controls for Employee Name, Employee
Id, Employment Status, Include, Supervisor Name, Job Title and Sub Unit, plus
Reset and Search controls. An employee-result table with column headers including
Id, First (& Middle) Name, Last Name, Job Title and Actions is visible.

## ORH-04 — Directory screen

Actor: an authenticated public-demo user.

Precondition: the Dashboard is open.

Main flow: select the Directory navigation link.

Expected outcome: the URL ends in `/web/index.php/directory/viewDirectory`. The
page shows a Directory heading; Employee Name, Job Title and Location filters;
Reset and Search controls; and directory result cards.

## ORH-05 — Directory Job Title listbox

Actor: an authenticated public-demo user.

Precondition: the Directory screen is open.

Main flow: activate the Job Title control showing `-- Select --`.

Expected outcome: a listbox opens and visibly offers `-- Select --` and observed
job-title options including `HR Manager`, `QA Engineer`, and `Software Engineer`.

## Clarifications deliberately not asserted

- Record totals, employee names, job-title options, and dashboard widget data are
  shared demo data and may change; they are not stable assertions except for the
  specifically observed UI labels above.
- No expected behavior for invalid login, saving, editing, deleting, or searching
  directory records was observed in this session. Those behaviours require a
  separate approved requirement before they are treated as test oracles.
