import logging
import logging.handlers
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
from psycopg2.extras import DictCursor # Useful for getting column names
from forms import RegistrationForm, LoginForm, PollForm, VoteForm, OrganizationForm
from flask_wtf.csrf import CSRFProtect, CSRFError
import json
import os
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', '1234_default_secret_key')
app.config['WTF_CSRF_ENABLED'] = True

csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- Logging Configuration ---
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.handlers.RotatingFileHandler(
    'logs/app.log', maxBytes=1024 * 1024 * 10, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

# --- Context Processor to inject current year ---
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.utcnow().year}

# --- Database Connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', ""),
            port=os.environ.get('DB_PORT', "5432"),
            user=os.environ.get('DB_USER', ""),
            password=os.environ.get('DB_PASSWORD', ""),
            database=os.environ.get('DB_NAME', "")
        )
        return conn
    except psycopg2.Error as e:
        app.logger.error(f"Error connecting to database: {e}")
        return None

# --- User Model and Functions ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.is_admin = user_data.get('is_admin', False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, username, password_hash, is_admin FROM "users" WHERE id = %s', (user_id,))
            user = cur.fetchone()
            if user: return {"id": user[0], "username": user[1], "password_hash": user[2], "is_admin": user[3]}
            return None
    except psycopg2.Error as e: app.logger.error(f"Error retrieving user by ID {user_id}: {e}"); return None
    finally:
        if conn: conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, username, password_hash, is_admin FROM "users" WHERE username = %s', (username,))
            user = cur.fetchone()
            if user: return {"id": user[0], "username": user[1], "password_hash": user[2], "is_admin": user[3]}
            return None
    except psycopg2.Error as e: app.logger.error(f"Error retrieving user by username {username}: {e}"); return None
    finally:
        if conn: conn.close()

def create_user(username, password, is_admin=False):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            hashed_password = generate_password_hash(password)
            cur.execute('INSERT INTO "users" (username, password_hash, is_admin) VALUES (%s, %s, %s)', (username, hashed_password, is_admin))
            conn.commit()
            return True
    except psycopg2.Error as e: app.logger.error(f"Error creating user {username}: {e}"); conn.rollback(); return False
    finally:
        if conn: conn.close()

def SCRIPT_create_initial_admin_user():
    admin_username = "admin"
    admin_password = "admin"
    with app.app_context():
        if not get_user_by_username(admin_username):
            app.logger.info(f"Creating initial admin user '{admin_username}'...")
            if create_user(admin_username, admin_password, is_admin=True):
                app.logger.info("Initial admin user created successfully.")
            else:
                app.logger.error("Failed to create initial admin user.")
        else:
            app.logger.info(f"Admin user '{admin_username}' already exists.")

def create_organization_db(name, acronym, logo_filename, description):
    """Inserts a new organization into the database."""
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO organization (name, acronym, logo_filename, description) VALUES (%s, %s, %s, %s)',
                (name, acronym, logo_filename, description)
            )
            conn.commit()
            return True
    except psycopg2.IntegrityError as e:
        app.logger.warning(f"Integrity error creating organization (likely exists): {e}")
        conn.rollback()
        return "exists" # Special return value to signal it exists
    except psycopg2.Error as e:
        app.logger.error(f"Error creating organization '{name}': {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- Organization Functions ---
def get_all_organizations():
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, acronym FROM organization ORDER BY name')
            orgs_raw = cur.fetchall()
            return [{"id": org[0], "name": org[1], "acronym": org[2]} for org in orgs_raw]
    except psycopg2.Error as e:
        app.logger.error(f"Error retrieving organizations: {e}")
        return []
    finally:
        if conn: conn.close()

# --- Poll and Vote Functions ---
def get_all_polls():
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.id, p.title, p.created_at, o.name as org_name, o.acronym as org_acronym, o.logo_filename as org_logo
                FROM poll p
                LEFT JOIN organization o ON p.organization_id = o.id
                ORDER BY p.created_at DESC
            ''')
            polls_raw = cur.fetchall()
            return [{"id": poll[0], "title": poll[1], "created_at": poll[2], "org_name": poll[3], "org_acronym": poll[4], "org_logo": poll[5]} for poll in polls_raw]
    except psycopg2.Error as e:
        app.logger.error(f"Error retrieving polls: {e}")
        return None
    finally:
        if conn: conn.close()

def create_poll_db(title, options, organization_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO poll (title, organization_id) VALUES (%s, %s) RETURNING id', (title, organization_id))
            poll_id = cur.fetchone()[0]
            for option_text in options:
                if option_text.strip():
                    cur.execute('INSERT INTO option (poll_id, text) VALUES (%s, %s)', (poll_id, option_text.strip()))
            conn.commit()
            return poll_id
    except psycopg2.Error as e:
        app.logger.error(f"Error creating poll '{title}' for org {organization_id}: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_poll_by_id(poll_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.id, p.title, p.created_at, o.name as org_name, o.acronym as org_acronym, o.logo_filename as org_logo
                FROM poll p
                LEFT JOIN organization o ON p.organization_id = o.id
                WHERE p.id = %s
            ''', (poll_id,))
            poll_data = cur.fetchone()
            if poll_data:
                cur.execute('SELECT id, text FROM option WHERE poll_id = %s ORDER BY id', (poll_id,))
                options_raw = cur.fetchall()
                return {"id": poll_data[0], "title": poll_data[1], "created_at": poll_data[2], "org_name": poll_data[3], "org_acronym": poll_data[4], "org_logo": poll_data[5], "options": [{"id": opt[0], "text": opt[1]} for opt in options_raw]}
            return None
    except psycopg2.Error as e:
        app.logger.error(f"Error retrieving poll {poll_id}: {e}")
        return None
    finally:
        if conn: conn.close()

def create_vote_db(user_id, option_id):
    conn = get_db_connection()
    if not conn: return False
    poll_id_for_vote = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT poll_id FROM option WHERE id = %s", (option_id,))
            result = cur.fetchone()
            if not result: return False
            poll_id_for_vote = result[0]
        with conn.cursor() as cur:
            cur.execute('INSERT INTO vote (user_id, option_id, poll_id) VALUES (%s, %s, %s)', (user_id, option_id, poll_id_for_vote))
            conn.commit()
            return True
    except psycopg2.IntegrityError: conn.rollback(); return False
    except psycopg2.Error as e: app.logger.error(f"Error creating vote: {e}"); conn.rollback(); return False
    finally:
        if conn: conn.close()

def get_vote_by_user_poll(user_id, poll_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT vote.id, vote.option_id FROM vote JOIN option ON vote.option_id = option.id WHERE vote.user_id = %s AND option.poll_id = %s''', (user_id, poll_id))
            vote_data = cur.fetchone()
            if vote_data: return {"vote_id": vote_data[0], "option_id": vote_data[1]}
            return None
    except psycopg2.Error as e: app.logger.error(f"Error retrieving vote: {e}"); return None
    finally:
        if conn: conn.close()

def get_option_votes(option_id):
    conn = get_db_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM vote WHERE option_id = %s', (option_id,))
            count = cur.fetchone()[0]
            return count
    except psycopg2.Error as e: app.logger.error(f"Error retrieving vote count: {e}"); return 0
    finally:
        if conn: conn.close()

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin:
            flash("You are not authorized to access this page.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
def index():
    all_polls_from_db = get_all_polls()
    polls_for_template = []
    if all_polls_from_db is None:
        flash("Could not retrieve recent polls due to a database issue.", "warning")
    else:
        polls_for_template = all_polls_from_db[:5]
    return render_template('index.html', polls=polls_for_template)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if get_user_by_username(form.username.data):
            flash('Username already exists.', 'danger')
        elif create_user(form.username.data, form.password.data):
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed due to a server error.', 'danger')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user_data = get_user_by_username(form.username.data)
        if user_data:
            user_obj = User(user_data)
            if user_obj.check_password(form.password.data):
                login_user(user_obj)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/create_poll', methods=['GET', 'POST'])
@admin_required
def create_poll_route():
    form = PollForm(request.form)
    organizations = get_all_organizations()
    form.organization.choices = [(org['id'], f"{org['name']} ({org['acronym']})") for org in organizations]
    form.organization.choices.insert(0, (0, '--- Select an Organization ---'))
    if request.method == 'POST':
        if form.organization.data == 0:
            form.organization.errors.append('You must select a conducting organization.')
        if form.validate_on_submit():
            title = form.title.data.strip()
            organization_id = form.organization.data
            options_json = request.form.get('options_data')
            if not options_json:
                flash("No poll options were submitted. Please add at least two options.", "danger")
                return render_template('create_poll.html', form=form)
            try:
                options = json.loads(options_json)
                valid_options = [opt.strip() for opt in options if opt.strip()]
                if len(valid_options) < 2:
                    flash("A poll must have at least two distinct non-empty options.", "danger")
                    return render_template('create_poll.html', form=form)
            except (json.JSONDecodeError, TypeError):
                flash("Invalid options format.", "danger")
                return render_template('create_poll.html', form=form)
            poll_id = create_poll_db(title, valid_options, organization_id)
            if poll_id:
                flash('Poll created successfully!', 'success')
                return redirect(url_for('vote', poll_id=poll_id))
            else:
                flash('Failed to create poll. Please check logs or try again.', 'danger')
    return render_template('create_poll.html', form=form)

@app.route('/polls')
@login_required
def view_polls():
    polls_list = get_all_polls()
    if polls_list is None:
        flash("Could not retrieve polls.", "warning")
        polls_list = []
    elif not polls_list:
        flash("No polls have been created yet.", "info")
    return render_template('view_polls.html', polls=polls_list)

@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
@login_required
def vote(poll_id):
    poll_details = get_poll_by_id(poll_id)
    if not poll_details:
        flash("Poll not found.", "danger")
        return redirect(url_for('view_polls'))
    form = VoteForm()
    form.option.choices = [(str(opt['id']), opt['text']) for opt in poll_details['options']]
    existing_vote_info = get_vote_by_user_poll(current_user.id, poll_id)
    if form.validate_on_submit():
        if existing_vote_info:
            flash('You have already voted in this poll.', 'warning')
            return redirect(url_for('view_results', poll_id=poll_id))
        option_id = int(form.option.data)
        if create_vote_db(current_user.id, option_id):
            flash('Your vote has been recorded.', 'success')
            return redirect(url_for('view_results', poll_id=poll_id))
        else:
            flash('Failed to record your vote. An error occurred.', 'danger')
    return render_template('vote.html', poll=poll_details, form=form, existing_vote_info=existing_vote_info)

@app.route('/results/<int:poll_id>')
@login_required
def view_results(poll_id):
    poll_details = get_poll_by_id(poll_id)
    if not poll_details:
        flash("Poll not found.", "danger")
        return redirect(url_for('view_polls'))
    option_counts = {}
    total_votes = 0
    for option_item in poll_details['options']:
        vote_count = get_option_votes(option_item['id'])
        option_counts[option_item['text']] = vote_count
        total_votes += vote_count
    chart_labels = list(option_counts.keys())
    chart_data_values = list(option_counts.values())
    results_with_percentage = []
    for option_text, count in option_counts.items():
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        results_with_percentage.append({"text": option_text, "count": count, "percentage": round(percentage, 2)})
    return render_template('results.html', poll=poll_details, results=results_with_percentage,
                           chart_labels=json.dumps(chart_labels), chart_data=json.dumps(chart_data_values), total_votes=total_votes)

# --- Admin Routes ---
@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    user_count, poll_count = 0, 0
    if not conn:
        flash("Database connection error. Dashboard statistics may be incomplete.", "danger")
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                user_count_result = cur.fetchone()
                if user_count_result: user_count = user_count_result[0]
                cur.execute("SELECT COUNT(*) FROM poll")
                poll_count_result = cur.fetchone()
                if poll_count_result: poll_count = poll_count_result[0]
        except psycopg2.Error as e:
            app.logger.error(f"Error fetching admin dashboard stats: {e}")
            flash("Error fetching dashboard data.", "warning")
        finally:
            if conn: conn.close()
    return render_template("admin/admin_dashboard.html", user_count=user_count, poll_count=poll_count)

@app.route("/admin/organizations")
@admin_required
def admin_organizations():
    organizations = get_all_organizations()
    return render_template('admin/admin_organizations.html', organizations=organizations)

@app.route('/admin/organizations/add', methods=['GET', 'POST'])
@admin_required
def admin_add_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        result = create_organization_db(
            name=form.name.data,
            acronym=form.acronym.data,
            logo_filename=form.logo_filename.data,
            description=form.description.data
        )
        if result is True:
            flash(f"Organization '{form.name.data}' created successfully.", "success")
            return redirect(url_for('admin_organizations'))
        elif result == "exists":
            flash("An organization with that name or acronym already exists.", "danger")
        else:
            flash("Failed to create organization due to a database error.", "danger")
    return render_template('admin/admin_add_organization.html', form=form)

@app.route('/admin/tables')
@admin_required
def admin_tables():
    conn = get_db_connection()
    tables_list = []
    if not conn:
        flash("Database connection error.", "danger")
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
                tables_list = [r[0] for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error retrieving tables for admin: {e}")
            flash("Error retrieving tables.", "danger")
        finally:
            if conn: conn.close()
    return render_template('admin/admin_tables.html', tables=tables_list)

@app.route('/admin/tables/<string:table_name>')
@admin_required
def admin_view_table(table_name):
    ALLOWED_TABLES = ['users', 'poll', 'option', 'vote', 'organization', 'settings']
    if table_name not in ALLOWED_TABLES:
        flash(f"Access to table '{table_name}' is not permitted.", "danger")
        return redirect(url_for('admin_tables'))
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "danger")
        return redirect(url_for('admin_tables'))
    headers = []
    rows = []
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100")
            rows = cur.fetchall()
            if rows:
                headers = list(rows[0].keys())
            elif cur.description:
                headers = [desc[0] for desc in cur.description]
    except psycopg2.Error as e:
        app.logger.error(f"Error fetching data from table '{table_name}': {e}")
        flash(f"Could not retrieve data from table '{table_name}'.", "danger")
    finally:
        if conn: conn.close()
    return render_template('admin/admin_view_table.html', table_name=table_name, headers=headers, rows=rows)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    users_list = []
    if not conn:
        flash("Database connection error.", "danger")
    else:
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT id, username, is_admin, created_at FROM users ORDER BY username')
                users_raw = cur.fetchall()
                users_list = [{"id": u[0], "username": u[1], "is_admin": u[2], "created_at": u[3]} for u in users_raw]
        except psycopg2.Error as e:
            app.logger.error(f"Error retrieving users for admin: {e}")
            flash("Error retrieving users.", "danger")
        finally:
            if conn: conn.close()
    return render_template('admin/admin_users.html', users=users_list)

@app.route('/admin/users/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash("You cannot change your own admin status.", "warning")
        return redirect(url_for('admin_users'))
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "danger")
        return redirect(url_for('admin_users'))
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT is_admin FROM users WHERE id = %s', (user_id,))
            user_record = cur.fetchone()
            if user_record:
                new_status = not user_record[0]
                cur.execute('UPDATE users SET is_admin = %s WHERE id = %s', (new_status, user_id))
                conn.commit()
                flash("Admin status for user updated successfully.", "success")
            else:
                flash("User not found.", "warning")
    except psycopg2.Error as e:
        app.logger.error(f"Error toggling admin status for user ID {user_id}: {e}")
        if conn: conn.rollback()
        flash("Error updating admin status.", "danger")
    finally:
        if conn: conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for('admin_users'))
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "danger")
        return redirect(url_for('admin_users'))
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user_to_delete = cur.fetchone()
            if not user_to_delete:
                flash(f"User with ID {user_id} not found.", "warning")
                return redirect(url_for('admin_users'))
            cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            flash(f"User '{user_to_delete[0]}' deleted successfully.", "success")
    except psycopg2.Error as e:
        app.logger.error(f"Error deleting user ID {user_id}: {e}")
        if conn: conn.rollback()
        flash("Error deleting user.", "danger")
    finally:
        if conn: conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    settings_keys = ['site_name', 'max_votes_per_user', 'results_visibility']
    conn = get_db_connection()
    if request.method == 'POST':
        if not conn:
            flash("Database connection error. Cannot save settings.", "danger")
            return redirect(url_for('admin_settings'))
        try:
            with conn.cursor() as cur:
                for key in settings_keys:
                    if key in request.form:
                        value = request.form.get(key)
                        cur.execute("UPDATE settings SET setting_value = %s, updated_at = CURRENT_TIMESTAMP WHERE setting_key = %s", (value, key))
                conn.commit()
            flash("Settings updated successfully.", "success")
        except psycopg2.Error as e:
            app.logger.error(f"Error updating settings in DB: {e}")
            if conn: conn.rollback()
            flash("Failed to update settings in the database.", "danger")
        finally:
            if conn: conn.close()
        return redirect(url_for('admin_settings'))
    current_settings = {}
    if not conn:
        flash("Database connection error. Cannot load current settings.", "warning")
        current_settings = {key: app.config.get(key.upper(), '') for key in settings_keys}
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT setting_key, setting_value FROM settings WHERE setting_key = ANY(%s)", (settings_keys,))
                for row in cur.fetchall():
                    current_settings[row[0]] = row[1]
            for key in settings_keys:
                if key not in current_settings:
                    current_settings[key] = app.config.get(key.upper(), '')
        except psycopg2.Error as e:
            app.logger.error(f"Error fetching settings from DB: {e}")
            flash("Error loading settings from the database. Displaying defaults.", "warning")
            current_settings = {key: app.config.get(key.upper(), '') for key in settings_keys}
        finally:
            if conn: conn.close()
    return render_template('admin/admin_settings.html', settings=current_settings)

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f"404 Not Found: {request.path} - {e}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500 Internal Server Error: {request.path} - {e}", exc_info=True)
    return render_template('errors/500.html'), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRF Error: {e.description} at {request.path}")
    flash(f'CSRF token error: {e.description}. Please try submitting the form again.', 'danger')
    return redirect(request.referrer or url_for('index'))

# --- App Startup ---
with app.app_context():
    try:
        SCRIPT_create_initial_admin_user()
    except Exception as e:
        app.logger.error(f"Error during startup script: {e}")

if __name__ == '__main__':
    app.run(debug=True)
