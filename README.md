# Finance Tracker Backend (Django)

## Overview

This repository contains the backend implementation of a Financial Tracker application built with Django. The system serves as the core infrastructure of the application, responsible for managing users’ financial records, transactions, payments, notifications, and security.

The backend enables users to record and track financial activities, pay bills, request payments from other users, and receive automated email notifications related to budgeting deadlines. Payment processing is fully integrated with Chapa, supporting multiple payment methods including direct payments, USSD-based requests, and bank transfers.

Security is handled using JWT-based authentication, ensuring safe and stateless access to protected resources.

---

## Technology Stack

* Django (Backend framework)
* PostgreSQL (Database)
* Docker & Docker Compose
* Celery (Asynchronous task processing)
* Gunicorn (Production-grade WSGI server)
* Chapa Payment Gateway
* JWT Authentication

---

## Prerequisites

Before running the project, ensure the following are installed and properly configured on your system:

* Python 3.12 (recommended)
* Docker and Docker Compose
* pip
* Virtual environment support (venv or equivalent)

---

## Environment Variables Configuration

This project uses environment variables to manage sensitive configuration values such as database credentials, API keys, and security settings. An `.env.example` file is provided in the repository to guide proper setup.

### Setup Instructions

1. Create a `.env` file in the project root directory.
2. Copy the contents of `.env.example` into the `.env` file.
3. Update the values according to your local or production environment.
4. Ensure the `.env` file is excluded from version control.

---

### Required Environment Variables

#### Database Configuration (PostgreSQL)

```env
POSTGRES_DB=f_db
```

Name of the PostgreSQL database.

```env
POSTGRES_USER=finance_db_admin
```

Database user with access privileges to the specified database.

```env
POSTGRES_PASSWORD=your_database_password
```

Password for the PostgreSQL database user.

```env
POSTGRES_HOST=localhost
```

Database host. Use `localhost` for local development or the Docker service name when running inside Docker.

```env
POSTGRES_PORT=5432
```

PostgreSQL port number.

---

#### Email Service Configuration (Brevo)

Used for sending automated email notifications such as budget deadline alerts.

```env
BREVO_API_KEY=get_api_key_from_brevo
```

API key obtained from the Brevo (Sendinblue) dashboard.

---

#### Django Security Settings

```env
SECRET_KEY=generate_a_random_length_30_string_for_this_value
```

Django secret key used for cryptographic signing. This value must remain private and should be randomly generated.

---

#### Payment Gateway Configuration (Chapa)

```env
CHAPA_PRIVATE_KEY=get_chapa_key
```

Private API key obtained from the Chapa developer dashboard. This key is required for all payment-related operations.

---

## Project Setup Instructions

Follow the steps below to run the application locally.

### 1. Create and Activate a Virtual Environment

It is recommended to use Python 3.12.

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 2. Install Python Dependencies

Once the virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Start Docker Services

Set up and run the required Docker services (such as the database):

```bash
docker compose up -d
```

Ensure Docker is running before executing this command.

### 4. Apply Database Migrations

Run Django migrations to initialize the database schema:

```bash
python manage.py migrate
```

### 5. Start the Application Server

Run the application using Gunicorn:

```bash
gunicorn finance_tracker.wsgi
```

### 6. Start Celery Worker

To enable the automatic scheduling system and email notifications, start the Celery worker:

```bash
celery -A finance_tracker worker -l info
```

---

## Automated Setup (Optional)

Alternatively, you can use the provided `script.sh` file to automatically set up the project.

### Steps

1. Ensure Docker is running correctly.
2. Download or locate the `script.sh` file.
3. Run the script:

```bash
source script.sh
```

This script automates the environment setup and project initialization process.

---

## Core Features

* Financial record management and transaction tracking
* Bill payments and payment request handling
* Full integration with the Chapa payment gateway

  * Direct payments
  * USSD-based payment requests
  * Bank payment support
* Automated email notifications when budget deadlines are reached
* Secure authentication and authorization using JWT tokens
* Asynchronous task handling using Celery

---

## Purpose

This backend acts as the backbone of the Financial Tracker application. It centralizes all financial operations, enforces business rules, ensures secure transactions, and guarantees timely notifications, enabling users to manage their finances efficiently and reliably.
