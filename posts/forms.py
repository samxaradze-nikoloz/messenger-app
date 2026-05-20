from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from .models import Post, Comment


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiImageField(forms.FileField):
    widget = MultipleFileInput
    default_error_messages = {
        'invalid_image': _('Upload a valid image. The file you uploaded was not a valid image.'),
        'max_num': _('Upload at most %(max_num)s images.'),
    }

    def __init__(self, *args, max_num=None, **kwargs):
        self.max_num = max_num
        super().__init__(*args, **kwargs)

    def to_python(self, data):
        if not data:
            return []
        if isinstance(data, list):
            return data
        return [data]

    def validate(self, data):
        super().validate(data)
        if not data:
            return
        if self.max_num is not None and len(data) > self.max_num:
            raise ValidationError(self.error_messages['max_num'], params={'max_num': self.max_num})
        for uploaded_file in data:
            if uploaded_file is None:
                raise ValidationError(self.error_messages['invalid_image'])
            content_type = getattr(uploaded_file, 'content_type', '')
            if not content_type.startswith('image/'):
                raise ValidationError(self.error_messages['invalid_image'])

    def run_validators(self, value):
        for uploaded_file in value or []:
            super().run_validators(uploaded_file)


class PostCreateForm(forms.ModelForm):
    images = MultiImageField(
        required=True,
        max_num=10,
        help_text='Select one or more images',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
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