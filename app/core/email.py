"""
Email service for sending password reset links and other notifications.
This is a placeholder implementation that logs to console.
In production, integrate with services like SendGrid, Mailgun, or AWS SES.
"""


class EmailService:
    """Email service for sending various types of emails."""

    def __init__(self):
        # TODO: Initialize email service (SMTP, SendGrid, etc.)
        pass

    async def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
        frontend_url: str = "https://your-frontend-app.com",
    ) -> bool:
        """
        Send password reset email with token.

        Args:
            email: Recipient email address
            reset_token: The reset token to include in the link
            frontend_url: Base URL of the frontend application

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # TODO: Replace with actual email sending logic
        print("=" * 60)
        print("PASSWORD RESET EMAIL")
        print("=" * 60)
        print(f"To: {email}")
        print("Subject: Password Reset Request")
        print(f"Reset Link: {reset_link}")
        print("=" * 60)
        print("Email content:")
        print(f"""
                Dear User,

                You have requested to reset your password. Please click the link below to reset your password:

                {reset_link}

                This link will expire in 10 minutes.

                If you did not request this password reset, please ignore this email.

                Best regards,
                Cosmetic Shop Team
        """)
        print("=" * 60)

        # For now, always return True (email "sent")
        return True

    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email to new users."""
        print("=" * 60)
        print("WELCOME EMAIL")
        print("=" * 60)
        print(f"To: {email}")
        print("Subject: Welcome to Cosmetic Shop!")
        print(f"Name: {name}")
        print("=" * 60)

        return True


# Global email service instance
email_service = EmailService()
