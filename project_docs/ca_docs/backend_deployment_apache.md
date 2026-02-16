# Deployment Guide: Course Allocation Backend (Apache Edition)

## 1. Introduction

This document provides a comprehensive, step-by-step guide for deploying the Course Allocation Backend application on a Linux server using a MySQL database. This guide is written for a server administrator and assumes minimal prior knowledge of the application stack.

The production environment will consist of:
- **Apache:** As a reverse proxy to handle incoming web traffic.
- **Gunicorn:** As a WSGI server to run the Python Flask application.
- **MySQL:** As the production database.
- **Systemd:** To manage the application process and ensure it runs continuously.

This guide primarily uses commands for **Debian/Ubuntu**. Notes are provided for **Fedora/RHEL** where commands differ.

---

## 2. Prerequisites

### 2.1. Server Preparation

1.  **Access Your Server:**
    Connect to your Linux server via SSH.

2.  **Update System Packages:**
    Ensure your server's package list and installed packages are up-to-date.
    ```bash
    # For Debian/Ubuntu
    sudo apt update && sudo apt upgrade -y

    # For Fedora/RHEL
    sudo dnf update -y
    ```

3.  **Install Essential Tools:**
    Install Python, the virtual environment tool, development tools for building packages, and Git.
    ```bash
    # For Debian/Ubuntu
    sudo apt install -y python3 python3-venv python3-dev build-essential git

    # For Fedora/RHEL
    sudo dnf install -y python3 python3-devel @development-tools git
    ```

### 2.2. Create a Dedicated Application User

For security, the application should not run as the `root` user. Let's create a dedicated user account named `course_app`.

```bash
sudo adduser course_app
```

You will be prompted to set a password and fill in user information. You can leave the information fields blank by pressing `Enter`.

---

## 3. Database Setup (MySQL)

We will use MySQL as the production database.

1.  **Install MySQL Server:**
    ```bash
    # For Debian/Ubuntu
    sudo apt install -y mysql-server

    # For Fedora/RHEL
    sudo dnf install -y mysql-server
    sudo systemctl start mysqld
    sudo systemctl enable mysqld
    ```

2.  **Secure the MySQL Installation:**
    Run the security script included with MySQL. It will ask you to set a root password, remove anonymous users, and disable remote root login. It is highly recommended to answer 'Yes' to these prompts.
    ```bash
    sudo mysql_secure_installation
    ```

3.  **Create the Database and Database User:**
    Log in to the MySQL interactive terminal as the root user.
    ```bash
    sudo mysql
    ```
    Now, run the following SQL commands to create the database and a user for our application. 

    ```sql
    -- Create the database for the application
    CREATE DATABASE course_allocation_db;

    -- Create a dedicated user for the application that can only connect from localhost
    CREATE USER 'course_app_user'@'localhost' IDENTIFIED BY 'EinTH8vpYB9fCww8';

    -- Grant all privileges on the new database to the new user
    GRANT ALL PRIVILEGES ON course_allocation_db.* TO 'course_app_user'@'localhost';

    -- Apply the changes
    FLUSH PRIVILEGES;

    -- Exit the mysql terminal
    EXIT;
    ```

---

## 4. Application Setup

Now we will switch to our dedicated user to set up the application code.

1.  **Log in as the Application User:**
    ```bash
    su - course_app
    ```

2.  **Clone the Application Repository:**
    Clone the project code from its Git repository into the user's home directory.
    ```bash
    
    git clone https://github.com/Ekediee/course-allocation-backend.git /home/course_app/course-allocation-backend
    ```
    *Note: If you are moving the files manually, ensure they are placed in `/home/course_app/course-allocation-backend`.*

3.  **Navigate to the Project Directory:**
    ```bash
    cd /home/course_app/course-allocation-backend
    ```

4.  **Create and Activate a Python Virtual Environment:**
    A virtual environment keeps the project's dependencies isolated.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    Your shell prompt should now be prefixed with `(venv)`.

5.  **Install Dependencies:**
    Install the required Python packages from `requirements.txt` and add Gunicorn for serving the application.
    ```bash
    pip install -r requirements.txt gunicorn
    ```

---

## 5. Application Configuration

The application uses a `.env` file for configuration. We need to create one for the production environment.

1.  **Create the `.env` file:**
    ```bash
    nano .env
    ```

2.  **Add Production Configuration:**
    Copy and paste the following content into the file. **You must replace the placeholder values.**

    ```ini
    # Flask Configuration
    FLASK_APP=run.py
    FLASK_ENV=production

    # IMPORTANT: Generate a strong, random key for security
    # Use the command: openssl rand -hex 32
    SECRET_KEY=z39ffchTKCaHrcKshTcPM0vsMaA2_inD6XzYOuKGPhQ

    # Database Connection URL for MySQL
    # Use the password you created in Step 3.3
    DATABASE_URL=mysql+pymysql://course_app_user:EinTH8vpYB9fCww8@localhost/course_allocation_db

    # JWT (Authentication) Configuration
    # IMPORTANT: Generate another strong, random key
    JWT_SECRET_KEY=z39ffchTKCaHrcKshTcPM0vsMaA2_inD6XzYOuKGPhQ
    JWT_COOKIE_SECURE=True
    JWT_COOKIE_CSRF_PROTECT=True
    ```

    - To generate the required secret keys, you can use `openssl rand -hex 32` in your terminal.
    - Press `Ctrl+X`, then `Y`, then `Enter` to save and exit `nano`.

### 5.1. Email Configuration (Important)

For features that require sending emails (such as password resets or notifications), you must configure the email server settings in the `.env` file. If email is not configured, these features will not work.

Add the following variables to your `.env` file, customized for your email provider (e.g., Gmail, SendGrid, or your own SMTP server):

```ini
# Email Sending Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password-or-app-key
MAIL_DEFAULT_SENDER=("Your App Name" <noreply@example.com>)
```

**Notes:**
-   `MAIL_USE_TLS` and `MAIL_USE_SSL` are mutually exclusive. Use the one required by your provider.
-   For services like Gmail, you may need to generate an "App Password" instead of using your regular account password.
-   The `MAIL_DEFAULT_SENDER` is the "From" address that will appear on outgoing emails.

### 6. Run Database Migrations

With the configuration in place, we can now set up the database schema using the existing migrations.

```bash
# Ensure your virtual environment is still active
flask db upgrade
```

This command will connect to the MySQL database and create all the necessary tables.

---

## 7. Setting Up the Gunicorn Service

To ensure the application runs reliably in the background, we will create a `systemd` service file for Gunicorn.

1.  **Exit from the `course_app` user session:**
    ```bash
    exit
    ```
    You should now be back in your `sudo` user session.

2.  **Create the Systemd Service File:**
    ```bash
    sudo nano /etc/systemd/system/course-allocation.service
    ```

3.  **Add the Service Configuration:**
    Copy and paste the following content into the file.

    ```ini
    [Unit]
    Description=Gunicorn instance to serve the Course Allocation Backend
    After=network.target

    [Service]
    User=course_app
    Group=www-data
    WorkingDirectory=/home/course_app/course-allocation-backend
    Environment="PATH=/home/course_app/course-allocation-backend/venv/bin"
    ExecStart=/home/course_app/course-allocation-backend/venv/bin/gunicorn --workers 3 --bind unix:course-allocation.sock -m 007 run:app

    [Install]
    WantedBy=multi-user.target
    ```

4.  **Start and Enable the Service:**
    ```bash
    sudo systemctl start course-allocation
    sudo systemctl enable course-allocation
    ```

5.  **Check the Service Status:**
    Verify that the service started without errors.
    ```bash
    sudo systemctl status course-allocation
    ```
    Look for a green `active (running)` status. If there are errors, you can check the logs with `sudo journalctl -u course-allocation`. Press `Q` to exit the status/log view.

---

## 8. Configure Apache as a Reverse Proxy

Apache will sit in front of our application, handling web traffic and forwarding it to Gunicorn.

1.  **Install Apache:**
    ```bash
    # For Debian/Ubuntu
    sudo apt install -y apache2

    # For Fedora/RHEL
    sudo dnf install -y httpd
    ```

2.  **Enable Apache Proxy Modules:**
    We need to enable the modules that allow Apache to act as a reverse proxy.
    ```bash
    # For Debian/Ubuntu
    sudo a2enmod proxy
    sudo a2enmod proxy_http
    sudo systemctl restart apache2

    # For Fedora/RHEL
    # These modules are typically enabled by default. If not, edit /etc/httpd/conf.modules.d/00-proxy.conf
    sudo systemctl restart httpd
    ```

3.  **Create an Apache Configuration File:**
    ```bash
    # For Debian/Ubuntu
    sudo nano /etc/apache2/sites-available/course-allocation.conf

    # For Fedora/RHEL
    sudo nano /etc/httpd/conf.d/course-allocation.conf
    ```

4.  **Add the Apache Configuration:**
    Copy and paste the following, replacing `your_domain_or_server_ip` with your server's public domain name or IP address.

    ```apache
    <VirtualHost *:80>
        ServerName your_domain_or_server_ip

        ProxyPreserveHost On
        ProxyPass / unix:/home/course_app/course-allocation-backend/course-allocation.sock|http://localhost/
        ProxyPassReverse / unix:/home/course_app/course-allocation-backend/course-allocation.sock|http://localhost/
    </VirtualHost>
    ```

5.  **Enable the Apache Site:**
    ```bash
    # For Debian/Ubuntu
    sudo a2ensite course-allocation.conf
    # It's good practice to disable the default config
    sudo a2dissite 000-default.conf
    
    # For Fedora/RHEL, the config is enabled by being in conf.d

    ```

6.  **Test and Restart Apache:**
    ```bash
    # For Debian/Ubuntu
    sudo apache2ctl configtest  # Test the configuration for syntax errors
    sudo systemctl restart apache2

    # For Fedora/RHEL
    sudo apachectl configtest
    sudo systemctl restart httpd
    ```

7.  **Adjust Firewall (if applicable):**
    If you are using a firewall like `ufw`, allow traffic to Apache.
    ```bash
    sudo ufw allow 'Apache Full'
    ```

---

## 9. Final Verification

The deployment should now be complete.

-   **Access the Application:** Open a web browser and navigate to `http://your_domain_or_server_ip`. You should not see the default Apache page or a 502 Bad Gateway error. While the backend may not have a frontend to display, a successful connection means the services are working together.

-   **Troubleshooting:**
    -   **503 Service Unavailable Error:** This usually means Apache can't communicate with Gunicorn. Check the status of the `course-allocation` service (`sudo systemctl status course-allocation`) and its logs (`sudo journalctl -u course-allocation`).
    -   **Other Errors:** Check the Apache error logs at `/var/log/apache2/error.log` (Debian/Ubuntu) or `/var/log/httpd/error_log` (Fedora/RHEL).

Your application is now deployed and running.

---

## 10. Future Updates and Scaling

As the application evolves, you will need to deploy updates. This section covers the process for deploying new code and scaling the application to handle more traffic.

### 10.1. Deploying Application Updates

Follow these steps to update the application with new code from the repository.

1.  **Log in as the Application User:**
    ```bash
    su - course_app
    ```

2.  **Navigate to the Project Directory:**
    ```bash
    cd /home/course_app/course-allocation-backend
    ```

3.  **Pull the Latest Code:**
    Fetch the latest changes from the main branch of your repository.
    ```bash
    git pull origin main
    ```
    *(Note: Replace `main` with your primary branch name if it's different, e.g., `master`)*

4.  **Activate the Virtual Environment:**
    ```bash
    source venv/bin/activate
    ```

5.  **Update Dependencies:**
    If new packages have been added to `requirements.txt`, install them.
    ```bash
    pip install -r requirements.txt
    ```

6.  **Run New Database Migrations:**
    If the update includes changes to the database model, apply the new migrations.
    ```bash
    flask db upgrade
    ```

7.  **Exit and Restart the Service:**
    Log out of the `course_app` user session and restart the application service to apply all changes.
    ```bash
    exit
    sudo systemctl restart course-allocation
    ```

### 10.2. Scaling the Application

There are two primary ways to scale the application:

#### A. Vertical Scaling

This involves increasing the resources (CPU, RAM) of the single server where the application is hosted. This is the simplest approach but has limits. If you find that the server's CPU or memory usage is consistently high, you may need to upgrade your server plan.

#### B. Horizontal Scaling

This involves distributing the load across multiple instances of the application.

1.  **Increase Gunicorn Workers:**
    The simplest form of horizontal scaling is to increase the number of Gunicorn worker processes on your existing server. This allows the application to handle more concurrent requests.

    -   **Edit the systemd service file:**
        ```bash
        sudo nano /etc/systemd/system/course-allocation.service
        ```
    -   **Adjust the `--workers` flag:** A common recommendation is `(2 * number_of_cpu_cores) + 1`. For a 2-core server, you might use 5 workers.
        ```ini
        # Example for 5 workers
        ExecStart=/home/course_app/course-allocation-backend/venv/bin/gunicorn --workers 5 --bind unix:course-allocation.sock -m 007 run:app
        ```
    -   **Reload and restart the service:**
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl restart course-allocation
        ```

2.  **Deploying to Multiple Servers:**
    For very high traffic, you can deploy the application across multiple identical servers. This involves:
    -   Provisioning new servers and following this entire deployment guide on each one.
    -   Ensuring all servers connect to the **same central MySQL database**. The database should be hosted on a dedicated, powerful server that all application servers can access.
    -   Setting up a **Load Balancer** (e.g., using Apache's `mod_proxy_balancer`, HAProxy, or a cloud provider's load balancer) to distribute incoming traffic evenly across your application servers.
