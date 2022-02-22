from django import forms
from .models import Post, Comment
from django.forms.widgets import Textarea, Select


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    widgets = {
        'text': Textarea,
        'group': Select,
    }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    widgets = {
        'text': Textarea,
    }
