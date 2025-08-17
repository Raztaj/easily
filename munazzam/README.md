# Munazzam (منظّم)

Munazzam is a local CRM and WhatsApp campaign management system designed for 'Easily' to streamline, target, and professionalize their communication.

## Features

- **Contact Management**: Add and view contacts.
- **Tagging**: Assign tags to contacts for easy filtering and grouping.
- **Campaign Management**: Create campaigns with custom messages targeted at specific contact tags.
- **Anti-Annoyance Shield**: Avoid sending the same campaign to the same contact multiple times.
- **Excel Export**: Export your finalized campaign list (phone numbers and personalized messages) to an `.xlsx` file compatible with external sending tools.
- **Dashboard**: Get an at-a-glance overview of your CRM data.

## Setup and Installation

These instructions will guide you through setting up the project to run on your local machine.

### 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage the project's dependencies.

```bash
# Navigate to the project directory
cd munazzam

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate
# On Windows:
# venv\\Scripts\\activate
```

### 2. Install Dependencies

Install the required Python packages using pip.

```bash
pip install -r requirements.txt
```

### 3. Configure the Application

Set the `FLASK_APP` environment variable to point to the application's entry point.

```bash
# On macOS and Linux:
export FLASK_APP=run.py
# On Windows:
# set FLASK_APP=run.py
```

### 4. Initialize the Database

Create the SQLite database and the necessary tables by running the `init-db` command.

```bash
flask init-db
```
This will create a `munazzam.sqlite` file inside an `instance` folder in your project directory.

### 5. Run the Application

You can now run the local development server.

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000` in your web browser.

## Testing

To run the application's test suite, you first need to install the development dependencies.

```bash
# Make sure your virtual environment is activated
pip install -r requirements-dev.txt
```

Then, you can run the tests using `pytest`.

```bash
pytest
```
