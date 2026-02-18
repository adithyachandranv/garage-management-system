# Garage Management System (GaragePro)

A comprehensive web-based application for managing a vehicle repair garage. This system streamlines operations for Admins, Mechanics, and Customers, covering everything from job scheduling and parts inventory to billing and approvals.

## 🚀 Features

### 👤 User Roles
-   **Admin**: Full control over the system. Manage users, jobs, inventory, billing, and view analytics.
-   **Mechanic**: View assigned jobs, diagnose issues, log repairs, request approvals, and track job status.
-   **Customer**: View separate dashboards for their vehicles, track job progress, approve/reject repair estimates, views invoices.

### 🛠 Core Modules

#### 1. Job Management
-   **Job Tracking**: End-to-end tracking from "Received" to "Delivered".
-   **Status Workflow**: `Received` -> `Diagnosing` -> `Waiting Approval` -> `In Progress` -> `Completed` -> `Delivered`.
-   **Assignment**: Admins can assign jobs to specific mechanics.
-   **Admin CRUD**: Admins can Edit and Delete job records directly.

#### 2. Repair & Diagnostics
-   **Repair Logs**: Mechanics log specific repairs with diagnosis, work done, and estimated costs.
-   **Iterative Workflow**: Mechanics can add repairs incrementally. Subsequent repairs require separate customer validation.

#### 3. Approval System
-   **Customer Approval**: Customers must approve repair estimates before work proceeds.
-   **Granular Control**: Approval requests bundle unapproved repairs.
-   **Status Updates**: Jobs move to `Waiting Approval` automatically when estimate is created, and back to `In Progress` upon approval.

#### 4. Inventory Management
-   **Parts Tracking**: Track stock levels, pricing, and SKUs.
-   **Low Stock Alerts**: Dashboard indicators for items below threshold.
-   **Stock Movements**: Log 'IN' (Restock) and 'OUT' (Usage) movements.

#### 5. Billing & Invoicing
-   **Auto-Invoicing**: Generates invoices based on **approved** repairs and parts used.
-   **Status Tracking**: Track Paid vs. Pending/Due invoices.
-   **Payment Recording**: Log payments against invoices.

#### 6. Notifications
-   **Real-time Alerts**: In-app notifications for job assignments, status changes, and approval requests.

## 📦 Project Structure

```
garage-management/
├── accounts/           # User authentication & role management
├── admin_portal/       # Forms & views specific to Admin actions
├── billing/            # Invoice & Payment models/views
├── core/               # Main dashboard & core logic
├── customers/          # Customer-facing views & vehicle mgmt
├── inventory/          # Parts & Stock management
├── jobs/               # Service Job logic & workflows
├── notifications/      # Notification system
├── repairs/            # Repair logging & diagnostics
├── templates/          # HTML Templates (Tailwind CSS styled)
└── manage.py           # Django CLI utility
```

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd garage-management
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install django pillow
    ```

4.  **Apply Migrations**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create Superuser (Admin)**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run Development Server**
    ```bash
    python manage.py runserver
    ```
    Access the app at `http://127.0.0.1:8000/`

## 🧪 Running Tests

The project includes a suite of tests to verify core logic (Billing, Approvals, Admin CRUD).

```bash
# Run all tests
python manage.py test

# Run specific test modules
python test_billing.py
python test_approval_flow.py
python test_notifications.py
```

## 📝 Usage Guide

### Logging In
-   **Admin**: Login to access the Admin Dashboard.
-   **Mechanic/Customer**: Use respective credentials.

### Common Workflows
1.  **New Job**: Admin creates a job -> Assigns Mechanic.
2.  **Diagnostics**: Mechanic diagnoses -> Adds Repair Log -> Requests Approval.
3.  **Approval**: Customer logs in -> Approves repair -> Status updates to `In Progress`.
4.  **Completion**: Mechanic finishes work -> Marks `Completed`.
5.  **Billing**: Admin generates Invoice -> Records Payment -> Marks `Delivered`.

---
*Built with Django & Tailwind CSS*
