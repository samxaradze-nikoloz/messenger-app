from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_rename_user_to_author'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='content',
            new_name='caption',
        ),
    ]
