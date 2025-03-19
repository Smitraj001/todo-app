from flask import Flask, redirect, url_for, session, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
from flask_mail import Mail, Message
from database import connect_db, get_tasks, add_task, update_task, delete_task  # ✅ Import SQLite3 functions

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure key

# Set up Google OAuth Flow
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Enable HTTP (for local testing)
GOOGLE_CLIENT_ID = "526413151802-h3575gp36db2phk5n9fikbab38k3q9js.apps.googleusercontent.com"  # Replace with your Client ID
client_secrets_file = "client_secret.json"

flow = Flow.from_client_secrets_file(
    client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile",
            "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Change to 465 for SSL
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True  # Enable SSL
app.config['MAIL_USERNAME'] = 'sszala8878@gmail.com'
app.config['MAIL_PASSWORD'] = 'uxlpzopnhazdjmyg '  # Use the generated App Password
app.config['MAIL_DEFAULT_SENDER'] = 'sszala8878@gmail.com'

mail = Mail(app)

# Function to send email notification
def send_email_notification(user_email, user_name, task_title=None):
    """Send a notification email from the user's email."""
    try:
        msg = Message("To-Do App Notification",
                      recipients=['smitraj07@gmail.com'],  # Send to admin or others
                      reply_to=user_email)  # User's email as reply-to

        if task_title:
            msg.body = f"Hello {user_name},\n\nA new task '{task_title}' has been added to your To-Do List!"
        else:
            msg.body = f"Hello {user_name},\n\nYou have successfully logged into the To-Do App!"

        mail.send(msg)
        print(f"✅ Email sent successfully from {user_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


# Routes
@app.route("/")
def UI():
    return render_template("UI.html")

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = google.auth.transport.requests.Request()
    user_info = id_token.verify_oauth2_token(credentials.id_token, request_session, GOOGLE_CLIENT_ID)

    session["user"] = user_info
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session['user']['email']
    user_name = session['user']['name']

    # Fetch tasks from the database
    tasks = get_tasks()

    # Send login email notification
    send_email_notification(user_email, user_name)

    return render_template("dashboard.html", tasks=tasks, user_name=user_name)

@app.route("/add_task", methods=["POST"])
def add_task_route():
    if "user" not in session:
        return redirect(url_for("login"))

    task_title = request.form.get("title")
    if task_title:
        add_task(task_title)

        # Send email notification about new task
        user_email = session["user"]["email"]
        user_name = session["user"]["name"]
        send_email_notification(user_email, user_name, task_title)

    return redirect(url_for("dashboard"))

@app.route("/update_task/<int:task_id>/<int:completed>")
def update_task_route(task_id, completed):
    if "user" not in session:
        return redirect(url_for("login"))

    update_task(task_id, completed)
    return redirect(url_for("dashboard"))

@app.route("/delete_task/<int:task_id>")
def delete_task_route(task_id):
    if "user" not in session:
        return redirect(url_for("login"))

    delete_task(task_id)
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()  # ✅ Clear session on logout
    return redirect(url_for("UI"))  # Redirect to UI instead of index

if __name__ == "__main__":
    app.run(debug=True)
