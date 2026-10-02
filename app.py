import os
from src import create_app, db
from src.models import User, Task, AuditLog, PasswordResetToken

app = create_app(os.environ.get("FLASK_ENV", "default"))


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Task": Task, "AuditLog": AuditLog, "PasswordResetToken": PasswordResetToken}



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
