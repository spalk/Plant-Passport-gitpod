from django import forms
from .models import Attribute, Plant, RichPlant, Photo
#from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import ModelForm


class PlantForm(forms.Form):
    
    def __init__(self, attributes_dic={}, *args, **kwargs):
        """
        Generate form fields for all plant attributes
        """
        super().__init__(*args, **kwargs)
        if attributes_dic:
            for attribute in Attribute.objects.all():
                self.fields[attribute.key] = forms.CharField(label=attribute.name, initial=attributes_dic[attribute.key],  max_length=100, required=False)    
        else: 
            for attribute in Attribute.objects.all():
                self.fields[attribute.key] = forms.CharField(label=attribute.name, max_length=100, required=False)    


class AttributeForm(forms.Form):

    def __init__(self, label=None, key=None, value=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if key:
            self.fields[key] = forms.CharField(label=label, initial=value, max_length=100, required=False)
        else:
            # why is this case possible?
            # should be 404 or something
            self.fields['attribute'] = forms.CharField(label='No label', max_length=100, required=False)


class PhotoForm(forms.ModelForm):
    
    class Meta:
        model = Photo
        fields = ('description', 'photo', 'user')


    
