AUTH-VOTE/
├── Admin_Console/
│   └── main.cpp
├── Backend/
│   ├── app.py
│   └── admin_tools.py 
├── Database/
│   └── Authvote_schema.sql
└── Frontend/
    ├── login.html
    ├── instructions.html
    ├── rapid_fire.html
    ├── voting_ballot.html
    └── dashboard.html

## Project overview

AuthVote is a student authentication and digital voting application.

### Main components

- `Frontend/` contains the voter pages and login screen.
- `Backend/` contains the application API and admin utilities.
- `Database/` contains the SQL schema used by the project.
- `Admin_Console/` contains the administrative console source.

### Working with the project

1. Review the backend and frontend configuration before running locally.
2. Set the required database connection details for your environment.
3. Start the backend service using the project's deployment configuration.
4. Serve the frontend pages through the configured web server.
5. Use the Jenkins pipeline to build and deploy a reviewed change.
