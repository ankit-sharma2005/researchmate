from django import forms


class TopicForm(forms.Form):
    topic = forms.CharField(
        label="Research topic",
        max_length=500,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "What would you like to research?",
                "autocomplete": "off",
                "autofocus": True,
            }
        ),
        error_messages={
            "required": "Enter a topic to start your research.",
            "max_length": "Keep your topic under 500 characters.",
        },
    )
