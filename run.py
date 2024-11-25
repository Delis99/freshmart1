from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Importing both applications
from employee_app.app import app as employee_app
from user_app.app import app as user_app

# Combine apps into a DispatcherMiddleware
application = DispatcherMiddleware(
    user_app,  # Primary application
    {
        '/employee': employee_app  # Employee app accessible at "/employee"
    }
)

if __name__ == "__main__":
    run_simple('localhost', 5000, application, use_reloader=True, use_debugger=True)


