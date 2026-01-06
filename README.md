# 🛒 FreshtMart

**Full-Stack Online Grocery Platform**

*CMPE 131 - Software Engineering I Course Project*

---

## 📋 Overview

FreshtMart is a course-based full-stack web application developed for CMPE 131 (Software Engineering I) at San José State University. The project simulates an online grocery platform and demonstrates foundational software engineering concepts, including backend development, database integration, and role-based application design.

The application was built using Python, Flask, HTML/CSS, and JavaScript, and is structured into multiple modules to support different user roles within the system.

---

## 🎯 Project Goals

- **Software Engineering Principles** – Apply core concepts in a real-world web application
- **Multi-Role System Design** – Separate workflows for users, employees, and delivery personnel
- **Backend Development** – Implement server-side logic using Flask
- **Database Integration** – Connect web application to a relational database
- **Team-Based Development** – Practice modular code organization and collaboration

---

## ✨ Features

### User-Facing Application
- Browse and search product catalog
- View product details and pricing
- Shopping cart functionality
- Order placement and tracking

### Employee Interface
- Internal operations management
- Product inventory control
- Order processing and fulfillment
- Administrative tools

### Delivery Module
- Order handling and logistics workflow
- Delivery status tracking
- Route management interface

### Core Functionality
- Backend routing and session handling using Flask
- Database connectivity for persistent data storage
- Role-based access control
- Request/response handling

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, Flask |
| **Frontend** | HTML, CSS, JavaScript |
| **Database** | SQL (via Flask integration) |

---

## 📁 Project Structure
```
FreshtMart/
├── user_app/              # User-facing application logic
├── employee_app/          # Employee workflows and internal tools
├── delivery_app/          # Delivery and order-handling features
├── app.py                 # Main Flask application entry point
├── db_connection.py       # Database connection and configuration
└── requirements.txt       # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)
- SQL database (MySQL, PostgreSQL, or SQLite)

### Installation

1. **Clone or download the project:**
```bash
   cd FreshtMart
```

2. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

3. **Configure database connection:**

   Update `db_connection.py` with your database credentials:
```python
   DB_HOST = 'localhost'
   DB_USER = 'your_username'
   DB_PASSWORD = 'your_password'
   DB_NAME = 'freshtmart'
```

4. **Initialize the database:**

   Run the provided SQL schema to create necessary tables.

### Running the Application

Start the Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🎓 Development Notes

This project represents early full-stack development work and focuses on understanding core concepts such as:

- **Request/Response Handling** – Processing HTTP requests in Flask
- **Modular Application Structure** – Organizing code by functional domains
- **Database-Backed Applications** – Persistent data storage and retrieval
- **Separation of Concerns** – Role-based architecture and access control
- **Session Management** – User authentication and state persistence

The codebase reflects learning objectives and design decisions appropriate for an introductory software engineering course.

---

## 📚 Key Learning Outcomes

### Software Engineering Concepts
- MVC (Model-View-Controller) architecture patterns
- RESTful API design principles
- Database schema design and normalization
- User authentication and authorization

### Technical Skills
- Python Flask framework
- SQL database operations
- Frontend-backend integration
- Session and cookie management
- Form validation and error handling

### Team Development
- Version control and collaboration
- Code modularization and reusability
- Documentation and code comments
- Testing and debugging strategies

---

## 🔧 Technical Highlights

- **Multi-Role Architecture** – Separate interfaces for users, employees, and delivery personnel
- **Database Integration** – Persistent storage for products, orders, and user data
- **Session Management** – Secure user authentication and role-based access
- **Modular Design** – Clean separation of concerns across application modules

---

## 📖 Course Context

**Course:** CMPE 131 - Software Engineering I  
**Institution:** San José State University

This project demonstrates foundational skills in full-stack web development that later evolved into more advanced systems, including distributed systems, networking protocols, and AI-driven applications.

---

## 🔮 Future Enhancements

Potential improvements for educational exploration:

- RESTful API implementation for mobile app integration
- Real-time order tracking with WebSockets
- Payment gateway integration
- Enhanced security features (CSRF protection, input sanitization)
- Responsive design for mobile devices
- Automated testing suite

---

## 📄 License

This project is provided for educational purposes.

---

## 🙏 Acknowledgments

- CMPE 131 course instructors and teaching assistants
- San José State University Computer Engineering Department
- Team members who contributed to the project

---

## 📧 Notes

This is a course project designed to demonstrate foundational software engineering concepts. The codebase prioritizes learning objectives and may not include all production-ready features or security measures.

---

**Built as part of Software Engineering I coursework** 📚
