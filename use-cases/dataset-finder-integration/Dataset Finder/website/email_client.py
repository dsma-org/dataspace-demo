from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'mail.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'no-reply-dataset-finder@example.com'
app.config['MAIL_PASSWORD'] = 'example_password'
app.config['MAIL_DEFAULT_SENDER'] = 'no-reply-dataset-finder@example.com'
mail = Mail(app)

def send_email_to_owner(reference, message, sender_mail, recipient_email):
    if not recipient_email:  # check if the recipient_email list is empty
        return "No contact data has been added."
    with app.app_context():
        msg = Message(f'RDMO Data Discovery Platform: {reference}',
                      recipients=recipient_email)

        automated_text = f"Dear Recipient,\n\n"\
                         f"This is an automated notification from the RDMO Data Discovery Platform. A user has attempted to contact you with the following message:\n"\
                         f"\n--- Message ---\n\n"\
                         f"\n"\
                         f"{message}\n"\
                         f"\n\n"\
                         f"--- End of Message ---\n"\
                         f"\n"\
                         f"If you wish to respond to the user, please use the following email address:\n"\
                         f"\n{sender_mail}\n"\
                         f"\n"\
                         f"Please note that your email address and any other personal data are kept confidential and are not visible to the sender.\n"\
                         f"\n"\
                         f"Thank you for using the RDMO Data Discovery Platform.\n"\
                         f"\n"\
                         f"Best regards,\n"\
                         f"RDMO Data Discovery Platform"
        
        msg.body = automated_text

        try:
            mail.send(msg)
            return 'E-Mail sent successfully!'
        except Exception as e:
            return "Oops! Something went wrong while sending the email. If you continue to encounter this issue, please don't hesitate to reach out to the data stewards for assistance at datastewards@iop.rwth-aachen.de. We apologize for any inconvenience caused."