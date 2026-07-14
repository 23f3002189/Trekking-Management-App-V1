# This is a Sample App for Trekking Management
# Trek Management System

It is a robust web platform built for streamlined outdoor adventure and trek management. It utilizes a secure role-based architecture specifically tailored for **Trekkers (Users)**, **Guides (Staff)**, and **Administrators**. The system efficiently handles complex operational logistics—including real-time slot capacity tracking, user access control, and dynamic staff assignments—while offering an intuitive frontend for booking and management.

---

## Features

### Administrator Controls
- **Analytics Dashboard:** Real-time 5-card overview tracking Total Revenue, All-Time Trekkers, Total Staff, and Active/Completed Treks.
- **Capacity Tracking:** Dynamic progress bars visualizing active trek occupancies.
- **Trek Management (CRUD):** Create, update, cancel, and assign staff to specific itineraries.
- **User & Staff Moderation:** Approve pending staff accounts, and blacklist/restore users to prevent unauthorized access.
- **Contextual Search:** Filter directories instantly without losing dashboard state.

### Guide (Staff) Interface
- **Assigned Treks:** A focused view showing only the treks the guide is assigned to lead.
- **Participant Manifests:** Instant access to crucial safety data, including emergency contact numbers and booking IDs for all participants on their assigned treks.

### Trekker (User) Experience
- **Available Treks Directory:** Browse upcoming treks with details on location, difficulty, dates, and remaining slots.
- **Dynamic Booking:** Select desired slots with automatic price calculation. Prevents overbooking automatically.
- **Personalized Profile:** View complete booking history and manage emergency contact information.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python, Flask, Flask-SQLAlchemy, Flask-Session |
| **Database** | SQLite (Default via SQLAlchemy) |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Jinja2 |
| **UI Components** | Bootstrap Flexbox, Modals, Tabs |
| **Icons** | Bootstrap Icons |

---

## 🗄️ Database Schema

The application uses SQLAlchemy ORM with the following core models:

### **User**
Handles authentication and role management.

- `id`
- `username`
- `email`
- `password`
- `role` (`admin`, `staff`, `user`)
- `is_approved`
- `full_name`
- `contact_number`
- `emergency_contact`
- `experience_years`
- `is_blacklisted`

### **Trek**
Stores trek itinerary information.

- `id`
- `name`
- `location`
- `difficulty`
- `start_date`
- `end_date`
- `price`
- `slots`
- `description`
- `staff_id`

Computed Properties:
- `booked_count`
- `available_slots`

### **Booking**
Maps users to treks.

- `id`
- `user_id`
- `trek_id`
- `slots_booked`
- `total_price`
- `booking_date`

### **Rating**
Stores feedback after trek completion.

- `id`
- `trek_id`
- `user_id`
- `staff_id`
- `rating`
- `review`

---

## Installation & Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/treksys.git
cd treksys
```

### 2. Create and Activate a Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install Flask Flask-SQLAlchemy Flask-Session Werkzeug
```

### 4. Run the Application

```bash
python app.py
```

### 5. Access the Application

Open your browser and navigate to:

```
http://localhost:5000
```

---

##  Security & Access Control

### Role-Based Routing
Backend routes explicitly verify `session['role']` to prevent unauthorized URL access (e.g., a Trekker attempting to access the Admin dashboard).

### Cross-Role Profile Viewing
Access permissions are enforced as follows:

- **Admins** can view every profile.
- **Guides** can only view participants assigned to their treks.
- **Trekkers** can only view their assigned guide.
- Unauthorized lateral profile access is blocked.

### Blacklist Protection
Suspended users are intercepted during the `/login` process, preventing access regardless of valid credentials.

### Booking Validation
- Prevents overbooking by validating available trek slots before confirming reservations.
- Automatically updates slot availability after every booking.

---

## 📁 Project Structure

```
treksys/
│── app.py
│── models.py
│── templates/
│── static/
│── instance/
│── README.md

```

