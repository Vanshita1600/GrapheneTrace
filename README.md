# GrapheneTrace

GrapheneTrace is a web-based application for monitoring and visualising patient pressure measurements. It provides dedicated interfaces for patients, clinicians and administrators to review measurement data, explore historical records and manage patient-related information.

## Features

- Role-based access for patients, clinicians and administrators
- Pressure measurement visualisation using charts and heatmaps
- Patient measurement history and comparison
- Alerts and key performance indicators
- Patient-clinician messaging
- CSV data processing
- JWT-based authentication
- SQL Server database integration

## Technologies

- **Frontend:** React, JavaScript, Bootstrap
- **Backend:** ASP.NET Core Web API, C#
- **Database:** Microsoft SQL Server
- **Data Access:** Entity Framework Core
- **Authentication:** JSON Web Tokens (JWT)

## Project Structure

- `GrapheneTraceApp.Api/` — Backend API, controllers, models and services
- `graphenetraceapp.client/` — React frontend
- `Database/` — Database SQL script
- `GrapheneTraceApp.sln` — Solution file

## Getting Started

### Backend

1. Configure the SQL Server connection string and JWT settings.
2. Navigate to the API project directory.
3. Restore dependencies and run the application.

```bash
dotnet restore
dotnet run
```

### Frontend

1. Navigate to the frontend directory.
2. Install dependencies and start the development server.

```bash
npm install
npm start
```

Ensure SQL Server is configured and the backend API is running before using the application. Adjust the frontend API configuration if necessary.

## Security Notice

Do not commit real patient data, credentials, signing keys or other sensitive information. Use secure configuration and sanitised sample data.

## Project Status

Developed as a software project demonstrating web application development, data visualisation, API integration and role-based access control.
