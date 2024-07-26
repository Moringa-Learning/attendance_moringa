# Attendance Taker
Attendance Taker is a web app designed to streamline the process of marking attendance. By using this tool, the time required to take attendance is reduced from 10-20 minutes to less than 3 minutes.

## Features
- User Registration and Authentication
- Add and Manage Students
- Generate Attendance Sheets in PDF format
- Track and Check Attendance
- View and Manage Generated PDFs

## Technologies Used
- Python 3.9
- Flask
- SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- PostgreSQL/SQLite
- Docker
- Docker Compose
- ReportLab

Incase you don't want to install postgresql, Could use the following [PostgreSQL Docker configuration](https://github.com/layersony/docker_postgres_dbs) 

## Getting Started
#### Prerequisites
- Docker
- Docker Compose

#### Installation
1. Clone the repository

##### For https
```bash

git clone https://github.com/Moringa-Learning/attendance_moringa.git
cd attendance_moringa
```
##### For ssh
```bash

git clone git@github.com:Moringa-Learning/attendance_moringa.git
cd attendance_moringa
```

2. Create and configure the .env file

Create a .env file in the root directory of your project and add the following variables:

```env

SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=your_database_uri
```
Replace `your_secret_key` with a secret key for your application and `your_database_uri` with the database URI for your PostgreSQL or SQLite database.
For local Testing you could either setup a SQLite database and use. Example of a database uri's
```env
# For SQLite

SQLALCHEMY_DATABASE_URI=sqlite:///exampleDatabase.db

# For PostgreSQL

SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://username:password@hostname:port/dbname'

```


3. Build and run the application using Docker Compose

```bash

docker-compose up --build -d
```
4. Access the application

Open your web browser and navigate to http://localhost:5000.

## To Run Tests
1. Ensure `SQLALCHEMY_DATABASE_URI` is configured
2. Open your Terminal and Ensure you are at the root folder then run
```bash
python -m unittest discover -s tests
```

## Usage
### User Registration
- Navigate to the registration page and create a new account.
### Login
- Login with your registered credentials.
### Add Students
- Add students by entering their email addresses.
### Generate PDF
- Generate a PDF template for attendance by specifying the number of days.
### Check Attendance
- Mark attendance by specifying which students are present.
### Manage Files
- View, download, or delete generated attendance PDFs.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

## License
This project is licensed under the [MIT License](LICENSE).

## Acknowledgements
- Flask Documentation
- Docker Documentation
- ReportLab Documentation