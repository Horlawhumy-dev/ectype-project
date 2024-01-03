from templated_mail.mail import BaseEmailMessage

from users.token import default_token_generator


class ActivationEmail(BaseEmailMessage):
    template_name = "email/activation.html"

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["token"] = default_token_generator.make_token(user)
        print(f"token: {context['token']} user: {user.email}")
        return context


class ConfirmationEmail(BaseEmailMessage):
    template_name = "email/confirmation.html"


class PasswordResetEmail(BaseEmailMessage):
    template_name = "email/password_reset.html"

    def get_context_data(self):
        # PasswordResetEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["token"] = default_token_generator.make_token(user)
        print(f"Context: {context['token']}")
        return context


class PasswordChangedConfirmationEmail(BaseEmailMessage):
    template_name = "email/password_changed_confirmation.html"
