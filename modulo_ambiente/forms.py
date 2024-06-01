from django import forms
from .models import ambiente

class dispo_form(forms.ModelForm):
    class Meta:
        model: ambiente
        fields = ['__all__']


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(required=False)
    excel_file = forms.FileField(required=False)