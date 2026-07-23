from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345678'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize DB and create default Admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin = User(username='admin', email='admin@trekking.com', password=hashed_password, role='admin', is_approved=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            if user.is_blacklisted:
                flash('Access Denied. Your account has been suspended.', 'danger')
                return redirect(url_for('login'))
            # 1. LOG THE USER IN 
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.full_name or user.username # Fallback to username
            
            flash(f'Welcome back, {session["name"]}!', 'success')
            # 2. ROUTE THEM BASED ON ROLE AND APPROVAL
            if user.role == 'admin': 
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'staff': 
                if not user.is_approved:
                    flash('Your staff account is pending admin approval. You can only view your profile for now.', 'info')
                    return redirect(url_for('profile')) # Redirect unapproved staff to profile
                return redirect(url_for('staff_dashboard'))
            else: 
                return redirect(url_for('user_dashboard'))
            
        flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] 
        contact_number = request.form['contact_number']
        emergency_contact = request.form['emergency_contact']
        
        # BACKEND VALIDATION
        if User.query.filter_by(username=username).first():
            flash('Error: Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register_user'))
            
        if User.query.filter_by(email=email).first():
            flash('Error: Email address is already registered. Please log in.', 'danger')
            return redirect(url_for('register_user'))
        
        # BACKEND VALIDATION: Check 10-digit rule for user
        if not contact_number.isdigit() or len(contact_number) != 10:
            flash('Error: Contact number must be exactly 10 digits.', 'danger')
            return redirect(url_for('register_user'))
            
        if not emergency_contact.isdigit() or len(emergency_contact) != 10:
            flash('Error: Emergency contact number must be exactly 10 digits.', 'danger')
            return redirect(url_for('register_user'))

        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        full_name = request.form['full_name']
        
        new_user = User(username=username, email=email, password=password, role='user', is_approved=True,
                        full_name=full_name, contact_number=contact_number, 
                        emergency_contact=emergency_contact)
        db.session.add(new_user)
        db.session.commit()
        flash('Trekker registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_user.html')

@app.route('/register/staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] 
        contact_number = request.form['contact_number']
        
        # BACKEND VALIDATION: Check for existing username or email
        if User.query.filter_by(username=username).first():
            flash('Error: Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register_staff'))
            
        if User.query.filter_by(email=email).first():
            flash('Error: Email address is already registered. Please log in.', 'danger')
            return redirect(url_for('register_staff'))
        
        # BACKEND VALIDATION: Check 10-digit rule for staff
        if not contact_number.isdigit() or len(contact_number) != 10:
            flash('Error: Contact number must be exactly 10 digits.', 'danger')
            return redirect(url_for('register_staff'))

        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        full_name = request.form['full_name']
        experience_years = request.form['experience_years']
        
        new_staff = User(username=username, email=email, password=password, role='staff', is_approved=False,
                         full_name=full_name, contact_number=contact_number, 
                         experience_years=experience_years)
        db.session.add(new_staff)
        db.session.commit()
        flash('Staff registration submitted! Awaiting Admin approval.', 'info')
        return redirect(url_for('login'))
    return render_template('register_staff.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    # Dashboard Metrics
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.date.desc()).limit(5).all()
    
    # Data for Management Tabs
    all_treks = Trek.query.all()
    all_users = User.query.filter_by(role='user').all()
    all_staff = User.query.filter_by(role='staff').all()
    
    # Search Query
    search_query = request.args.get('q', '')
    active_tab = request.args.get('tab', 'overview')
    
    if search_query:
        all_treks = Trek.query.filter(Trek.name.contains(search_query)).all()
        all_users = User.query.filter(User.role == 'user', User.username.contains(search_query)).all()
        all_staff = User.query.filter(User.role == 'staff', User.username.contains(search_query)).all()

    return render_template('admin_dashboard.html', 
                           total_treks=total_treks, total_users=total_users, 
                           total_staff=total_staff, total_bookings=total_bookings,
                           recent_bookings=recent_bookings, all_treks=all_treks, 
                           all_users=all_users, all_staff=all_staff, 
                           search_query=search_query, active_tab=active_tab)


@app.route('/admin/trek/add', methods=['POST'])
def add_trek():
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))

    start_date_obj = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    if start_date_obj < datetime.today().date():
        flash('Error: You cannot create a trek with a start date in the past.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if start_date_obj >= end_date_obj:
        flash('Error: The Start Date must be before the End Date.', 'danger')
        return redirect(url_for('admin_dashboard', tab='treks'))
    
    # Create and save the Trek
    new_trek = Trek(
        name=request.form['name'],
        location=request.form['location'],
        difficulty=request.form['difficulty'],
        duration=request.form['duration'],
        slots=request.form['slots'],
        start_date=start_date_obj,
        end_date=end_date_obj,
        description=request.form['description'],
        price=float(request.form['price'])
    )
    
    db.session.add(new_trek)
    db.session.commit()
    
    flash('Trek added successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='treks'))

@app.route('/admin/trek/delete/<int:trek_id>', methods=['POST'])
def delete_trek(trek_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    
    # Do not allow canceling Started or Completed treks
    if trek.status in ['Started', 'Completed']:
        flash(f'Cannot cancel a trek that is already {trek.status}.', 'danger')
        return redirect(url_for('admin_dashboard', tab='treks'))
    
    trek.status = 'Canceled'
    
    db.session.commit()
    flash('Trek has been canceled.', 'info')
    return redirect(url_for('admin_dashboard', tab='treks'))

@app.route('/admin/trek/assign/<int:trek_id>', methods=['POST'])
def assign_staff(trek_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    trek.staff_id = request.form['staff_id']
    db.session.commit()
    flash('Staff assigned to trek successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='treks'))

@app.route('/admin/user/toggle_status/<int:user_id>/<action>', methods=['POST'])
def toggle_user_status(user_id, action):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    
    if action == 'approve':
        user.is_approved = True
        flash(f'Staff {user.username} approved.', 'success')
    elif action == 'blacklist':
        user.is_blacklisted = True
        flash(f'User {user.username} blacklisted.', 'warning')
    elif action == 'restore':
        user.is_blacklisted = False
        flash(f'User {user.username} restored.', 'success')
        
    db.session.commit()
    return redirect(url_for('admin_dashboard', tab='users'))

@app.route('/admin/trek/edit/<int:trek_id>', methods=['POST'])
def edit_trek(trek_id):
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    
    if trek.status in ['Started', 'Completed']:
        flash(f'Error: Cannot edit "{trek.name}" because it is currently marked as {trek.status}.', 'danger')
        return redirect(url_for('admin_dashboard', tab='treks'))
    
    # Parse the dates
    start_date_obj = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    
    # Validation: Ensure Start Date is before End Date
    if start_date_obj >= end_date_obj:
        flash('Error: The Start Date must be before the End Date.', 'danger')
        return redirect(url_for('admin_dashboard', tab='treks'))
        
    trek.name = request.form['name']
    trek.location = request.form['location']
    trek.difficulty = request.form['difficulty']
    trek.duration = request.form['duration']
    trek.slots = request.form['slots']
    trek.start_date = start_date_obj
    trek.end_date = end_date_obj
    trek.price = float(request.form['price'])
    trek.description = request.form['description']
    trek.status = request.form['status'] 
    
    db.session.commit()
    flash(f'Trek "{trek.name}" updated successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='treks'))



# VIEW USER PROFILE (Shared: Admin and Staff)
@app.route('/profile/<int:user_id>')
def view_user_profile(user_id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
        
    user_to_view = User.query.get_or_404(user_id)
    current_role = session.get('role')
    
    # Access Control Logic
    if session['user_id'] != user_id and current_role != 'admin':
        
        # Block Users from viewing other Users
        if current_role == 'user' and user_to_view.role == 'user':
            flash('Unauthorized access. You cannot view other trekkers.', 'danger')
            return redirect(url_for('user_dashboard'))
            
        # Block Staff from viewing other Staff
        if current_role == 'staff' and user_to_view.role == 'staff':
            flash('Unauthorized access. You cannot view other staff profiles.', 'danger')
            return redirect(url_for('staff_dashboard'))
    return render_template('profile.html', 
                           user=user_to_view, 
                           Rating=Rating, 
                           Trek=Trek, 
                           Booking=Booking)


@app.route('/profile')
def profile():
    if not session.get('user_id'):
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    current_user = User.query.get(session['user_id'])
    
    return render_template('profile.html',Rating=Rating, user=current_user, Trek=Trek, Booking=Booking)
    
@app.route('/staff')
def staff_dashboard():
    if session.get('role') != 'staff': 
        return redirect(url_for('login'))
    # Block unapproved staff from accessing the dashboard directly
    user = User.query.get(session['user_id'])
    if not user.is_approved:
        flash('Your account is still pending admin approval. Dashboard access is restricted.', 'warning')
        return redirect(url_for('profile'))

    # Fetch only treks assigned to this specific staff member
    assigned_treks = Trek.query.filter_by(staff_id=session['user_id']).all()
    
    # Calculate Dashboard Metrics
    total_assigned = len(assigned_treks)
    open_treks = sum(1 for trek in assigned_treks if trek.status == 'Open')
    total_participants = sum(len(trek.bookings) for trek in assigned_treks if trek.bookings)

    return render_template('staff_dashboard.html', 
                           treks=assigned_treks, 
                           total_assigned=total_assigned,
                           open_treks=open_treks,
                           Rating=Rating,
                           total_participants=total_participants)

@app.route('/staff/trek/update/<int:trek_id>', methods=['POST'])
def staff_update_trek(trek_id):
    if session.get('role') != 'staff': 
        return redirect(url_for('login'))
        
    # Block unapproved staff
    user = User.query.get(session['user_id'])
    if not user.is_approved:
        flash('Your account is still pending admin approval.', 'warning')
        return redirect(url_for('profile'))
    
    trek = Trek.query.get_or_404(trek_id)
    
    # BACKEND SECURITY: Ensure this staff member actually owns this trek
    if trek.staff_id != session['user_id']:
        flash('Unauthorized action. You can only manage your own assigned treks.', 'danger')
        return redirect(url_for('staff_dashboard'))
        
    trek.status = request.form['status']
    trek.slots = int(request.form['slots'])
    
    db.session.commit()
    flash(f'Trek "{trek.name}" has been updated.', 'success')
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/rate_user/<int:trek_id>/<int:user_id>', methods=['POST'])
def rate_user(trek_id, user_id):
    if session.get('role') != 'staff': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != session['user_id'] or trek.status != 'Completed':
        flash('Unauthorized or trek not completed.', 'danger')
        return redirect(url_for('staff_dashboard'))
        
    existing = Rating.query.filter(Rating.trek_id == trek_id, Rating.user_id == user_id, Rating.staff_id == session['user_id'], Rating.user_rating != None).first()
    if existing:
        flash('You have already rated this user for this trek.', 'warning')
        return redirect(url_for('staff_dashboard'))
        
    rating = Rating(
        trek_id=trek_id,
        user_id=user_id,
        staff_id=session['user_id'],
        user_rating=request.form.get('rating'),
        comment=request.form.get('comment')
    )
    db.session.add(rating)
    db.session.commit()
    flash('User rating submitted.', 'success')
    return redirect(url_for('staff_dashboard'))

@app.route('/user')
def user_dashboard():
    if session.get('role') != 'user': 
        return redirect(url_for('login'))
    
    # 1. Fetch all bookings for the user to split into history sections
    all_bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    current_bookings = [b for b in all_bookings if b.trek.status != 'Completed']
    past_bookings = [b for b in all_bookings if b.trek.status == 'Completed']
    
    # 2. Start base query for Available treks (Search and Filter)
    query = Trek.query.filter_by(status='Open')
    
    search_query = request.args.get('q', '')
    difficulty_filter = request.args.get('difficulty', '')
    
    if search_query:
        query = query.filter((Trek.name.contains(search_query)) | (Trek.location.contains(search_query)))
    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)
        
    available_treks = query.all()
    
    return render_template('user_dashboard.html', 
                           current_bookings=current_bookings,
                           past_bookings=past_bookings,
                           treks=available_treks,
                           search_query=search_query,
                           difficulty_filter=difficulty_filter,
                           User=User,
                           Rating=Rating)

@app.route('/rate_staff/<int:trek_id>', methods=['POST'])
def rate_staff(trek_id):
    if session.get('role') != 'user': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    if trek.status != 'Completed':
        flash('You can only rate after the trek is completed.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    existing = Rating.query.filter(Rating.trek_id == trek_id, Rating.user_id == session['user_id'], Rating.staff_rating != None).first()
    if existing:
        flash('You have already submitted a rating for this trek.', 'warning')
        return redirect(url_for('user_dashboard'))
        
    rating = Rating(
        trek_id=trek_id,
        staff_id=trek.staff_id,
        user_id=session['user_id'],
        staff_rating=request.form.get('rating'),
        comment=request.form.get('comment')
    )
    db.session.add(rating)
    db.session.commit()
    flash('Rating submitted anonymously.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/book/<int:trek_id>', methods=['POST'])
def book_trek(trek_id):
    if session.get('role') != 'user': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    slots_requested = int(request.form.get('slots_to_book', 1))
    
    if trek.available_slots >= slots_requested:
        total_cost = trek.price * slots_requested
        
        new_booking = Booking(
            user_id=session['user_id'], 
            trek_id=trek_id,
            slots_booked=slots_requested,
            total_price=total_cost
        )
        db.session.add(new_booking)
        db.session.commit()
        
        flash(f'Successfully booked {slots_requested} slots for {trek.name}! Total: ₹{total_cost}', 'success')
    else:
        flash('Not enough slots available for this booking.', 'danger')
        
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)