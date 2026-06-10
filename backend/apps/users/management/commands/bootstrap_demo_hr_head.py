from django.core.management.base import BaseCommand, CommandError

from apps.users.models import User


class Command(BaseCommand):
    help = 'Create or update a demo HR-head account for local FYP demonstrations.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='hr-head.demo@hrrecruit.test', help='Demo HR-head login email.')
        parser.add_argument('--password', default='DemoPass123!', help='Demo HR-head login password.')
        parser.add_argument('--full-name', default='Demo HR Head', help='Demo HR-head display name.')
        parser.add_argument('--phone-number', default='+60000000000', help='Demo HR-head phone number.')
        parser.add_argument('--no-update-password', action='store_true', help='Do not reset the password for an existing user.')

    def handle(self, *args, **options):
        email = User.objects.normalize_email(options['email'])
        password = options['password']
        if not password:
            raise CommandError('Password must not be empty.')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': options['full_name'],
                'phone_number': options['phone_number'],
                'role': User.Role.HR_HEAD,
                'is_active': True,
            },
        )
        update_fields = []
        if not created:
            if user.role != User.Role.HR_HEAD:
                user.role = User.Role.HR_HEAD
                update_fields.append('role')
            if user.full_name != options['full_name']:
                user.full_name = options['full_name']
                update_fields.append('full_name')
            if user.phone_number != options['phone_number']:
                user.phone_number = options['phone_number']
                update_fields.append('phone_number')
            if not user.is_active:
                user.is_active = True
                update_fields.append('is_active')

        if created or not options['no_update_password']:
            user.set_password(password)
            update_fields.append('password')

        if update_fields:
            user.save(update_fields=sorted(set(update_fields)))

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} demo HR-head account: {email}'))
        self.stdout.write('Use this account to log in, create the demo organization, and add recruiter/interviewer users.')
