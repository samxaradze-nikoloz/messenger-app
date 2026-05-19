from django import forms
from .models import Post, Comment


class PostCreateForm(forms.ModelForm):
    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=True,
        help_text='Select one or more images'
    )

    class Meta:
        model = Post
        fields = ('caption',)
        widgets = {
            'caption': forms.Textarea(attrs={
                'placeholder': 'Write a caption…',
                'rows': 4,
                'maxlength': 2200,
            })
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)
        widgets = {
            'body': forms.TextInput(attrs={'placeholder': 'Add a comment…'})
        }