import os
import smtplib

from utils.datetime_utils import utc_now


class NotificationService:
    def __init__(self, host=None, port=None, username=None, password=None):
        self.notifications = []
        self.email_host = host or os.getenv("TASK_MANAGER_SMTP_HOST")
        self.email_port = int(port or os.getenv("TASK_MANAGER_SMTP_PORT", "587"))
        self.email_user = username or os.getenv("TASK_MANAGER_SMTP_USER")
        self.email_password = password or os.getenv("TASK_MANAGER_SMTP_PASSWORD")

    def send_email(self, to, subject, body):
        if not all((self.email_host, self.email_user, self.email_password)):
            return False
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(self.email_user, to, message)
            return True
        except (OSError, smtplib.SMTPException):
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você."
            f"\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        )
        sent = self.send_email(user.email, subject, body)
        if sent:
            self.notifications.append(
                {
                    "type": "task_assigned",
                    "user_id": user.id,
                    "task_id": task.id,
                    "timestamp": utc_now(),
                }
            )
        return sent

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!"
            f"\n\nData limite: {task.due_date}"
        )
        return self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [
            notification
            for notification in self.notifications
            if notification["user_id"] == user_id
        ]
