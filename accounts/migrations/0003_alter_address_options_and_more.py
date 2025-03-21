# Generated by Django 5.1.7 on 2025-03-18 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_address_options_remove_address_address_line_1_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ['-is_default', '-created_at'], 'verbose_name_plural': 'Addresses'},
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='phone_number',
            new_name='phone',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='profile_image',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_line1',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_line2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='city',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(choices=[('US', 'United States'), ('CA', 'Canada'), ('GB', 'United Kingdom')], default='US', max_length=2),
        ),
        migrations.AlterField(
            model_name='address',
            name='postal_code',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.CharField(max_length=100),
        ),
    ]
