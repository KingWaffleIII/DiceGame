from django import forms

from . import models


def has_special_char(text: str) -> bool:
    return any(c for c in text if not c.isalnum() and not c.isspace())


class LoginForm(forms.Form):
    name = forms.CharField(
        label="Username:",
        max_length=16,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Password:",
        max_length=16,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        name = cleaned_data.get("name")
        password = cleaned_data.get("password")

        try:
            user = models.User.objects.get(username=name)

            if not user.check_password(password):
                self.add_error("password", "Invalid name or password.")
        except models.User.DoesNotExist:
            self.add_error(
                "name",
                "No account was found with this username. Please signup instead.",
            )

        return cleaned_data


class SignUpForm(forms.Form):
    name = forms.CharField(
        label="Username:",
        max_length=16,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Password:",
        max_length=16,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="Confirm password:",
        max_length=16,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        try:
            models.User.objects.get(username=cleaned_data.get("name"))
            self.add_error("name", "Username is already in use! Please login instead.")
        except models.User.DoesNotExist:
            pass

        if password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match!")

        #! idrc ab security for a thing like this
        # if len(password) < 8:
        #     self.add_error("password", "Password must be at least 8 characters long!")

        # if not any(char.isdigit() for char in password):
        #     self.add_error("password", "Password must contain at least one number!")

        # if not has_special_char(password):
        #     self.add_error(
        #         "password", "Password must contain at least one special character!"
        #     )

        return cleaned_data
