from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('evaluations', '0003_unique_interview_evaluation_per_interviewer')]
    operations = [
        migrations.AddField(model_name='interviewrecording', name='audio_sha256', field=models.CharField(blank=True, db_index=True, max_length=64)),
        migrations.AddField(model_name='interviewrecording', name='upload_seconds', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='interviewtranscript', name='processing_error', field=models.TextField(blank=True)),
        migrations.AddField(model_name='interviewtranscript', name='processing_status', field=models.CharField(choices=[('PENDING','Pending'),('PROCESSING','Processing'),('COMPLETED','Completed'),('FAILED','Failed')], db_index=True, default='PENDING', max_length=12)),
        migrations.AlterField(model_name='interviewtranscript', name='transcript_text', field=models.TextField(blank=True)),
    ]
