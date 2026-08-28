from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Role

User = get_user_model()


def make_user(username='casey', role=Role.STUDENT, password='cornflower-pylon-83', **extra):
    return User.objects.create_user(
        username=username,
        email=extra.pop('email', f'{username}@example.com'),
        password=password,
        first_name=extra.pop('first_name', 'Casey'),
        last_name=extra.pop('last_name', 'Rivera'),
        role=role,
        **extra,
    )


class UserModelTests(TestCase):
    def test_new_users_default_to_student(self):
        self.assertEqual(User.objects.create_user(username='a', email='a@e.com').role, Role.STUDENT)

    def test_role_predicates_match_the_role(self):
        teacher = make_user(role=Role.TEACHER)
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_student)

    def test_display_name_falls_back_to_username(self):
        user = make_user(first_name='', last_name='')
        self.assertEqual(user.display_name, 'casey')

    def test_initials_use_first_and_last_name(self):
        self.assertEqual(make_user().initials, 'CR')

    def test_email_must_be_unique(self):
        make_user(username='one', email='shared@example.com')
        with self.assertRaises(Exception):
            make_user(username='two', email='shared@example.com')


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_login_with_username(self):
        ok = self.client.login(username='casey', password='cornflower-pylon-83')
        self.assertTrue(ok)

    def test_login_with_email(self):
        ok = self.client.login(username='casey@example.com', password='cornflower-pylon-83')
        self.assertTrue(ok)

    def test_login_with_email_is_case_insensitive(self):
        ok = self.client.login(username='CASEY@example.com', password='cornflower-pylon-83')
        self.assertTrue(ok)

    def test_wrong_password_is_rejected(self):
        self.assertFalse(self.client.login(username='casey', password='wrong'))

    def test_unknown_user_is_rejected(self):
        self.assertFalse(self.client.login(username='nobody@example.com', password='whatever'))

    def test_inactive_user_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()
        self.assertFalse(self.client.login(username='casey', password='cornflower-pylon-83'))

    def test_failed_login_shows_an_error_summary(self):
        response = self.client.post(
            reverse('login'), {'username': 'casey', 'password': 'wrong'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error-summary')

    def test_successful_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'casey', 'password': 'cornflower-pylon-83'},
        )
        self.assertRedirects(response, reverse('dashboard'))


class RegistrationTests(TestCase):
    payload = {
        'first_name': 'Dana',
        'last_name': 'Okonkwo',
        'username': 'dana',
        'email': 'dana@example.com',
        'role': Role.TEACHER,
        'phone': '',
        'password1': 'cornflower-pylon-83',
        'password2': 'cornflower-pylon-83',
    }

    def test_register_page_renders(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def test_registration_creates_user_and_signs_them_in(self):
        response = self.client.post(reverse('register'), self.payload)
        self.assertRedirects(response, reverse('dashboard'))

        user = User.objects.get(username='dana')
        self.assertEqual(user.role, Role.TEACHER)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_registration_rejects_the_admin_role(self):
        response = self.client.post(reverse('register'), {**self.payload, 'role': Role.ADMIN})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='dana').exists())

    def test_registration_rejects_a_duplicate_email(self):
        make_user(username='existing', email='dana@example.com')
        response = self.client.post(reverse('register'), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_email_is_stored_lowercase(self):
        self.client.post(reverse('register'), {**self.payload, 'email': 'Dana@Example.COM'})
        self.assertTrue(User.objects.filter(email='dana@example.com').exists())

    def test_signed_in_users_are_sent_to_the_dashboard(self):
        self.client.force_login(make_user())
        self.assertRedirects(self.client.get(reverse('register')), reverse('dashboard'))


class DashboardTests(TestCase):
    def test_dashboard_requires_sign_in(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_each_role_gets_its_own_dashboard(self):
        expected = {
            Role.ADMIN: 'accounts/dashboards/admin.html',
            Role.TEACHER: 'accounts/dashboards/teacher.html',
            Role.STUDENT: 'accounts/dashboards/student.html',
            Role.PARENT: 'accounts/dashboards/parent.html',
        }
        for role, template in expected.items():
            with self.subTest(role=role):
                self.client.force_login(make_user(username=f'u-{role}', role=role))
                response = self.client.get(reverse('dashboard'))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)

    def test_admin_dashboard_counts_accounts_by_role(self):
        admin = make_user(username='root', role=Role.ADMIN)
        make_user(username='t1', role=Role.TEACHER)
        make_user(username='s1', role=Role.STUDENT)
        make_user(username='s2', role=Role.STUDENT)

        self.client.force_login(admin)
        context = self.client.get(reverse('dashboard')).context

        self.assertEqual(context['user_count'], 4)
        self.assertEqual(context['teacher_count'], 1)
        self.assertEqual(context['student_count'], 2)
        self.assertEqual(context['parent_count'], 0)

    def test_admin_nav_is_hidden_from_students(self):
        self.client.force_login(make_user())
        self.assertNotContains(self.client.get(reverse('dashboard')), 'Manage users')


class RoleDecoratorTests(TestCase):
    """The decorator is exercised through a URLconf built for the test."""

    def test_anonymous_visitor_is_sent_to_login(self):
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        from .decorators import teacher_required

        @teacher_required
        def view(request):
            raise AssertionError('view should not run')

        request = RequestFactory().get('/staff/')
        request.user = AnonymousUser()

        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_wrong_role_is_redirected_to_own_dashboard(self):
        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.test import RequestFactory

        from .decorators import teacher_required

        @teacher_required
        def view(request):
            raise AssertionError('view should not run')

        request = RequestFactory().get('/staff/')
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        request.user = make_user(role=Role.STUDENT)

        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_matching_role_reaches_the_view(self):
        from django.http import HttpResponse
        from django.test import RequestFactory

        from .decorators import teacher_required

        @teacher_required
        def view(request):
            return HttpResponse('ok')

        request = RequestFactory().get('/staff/')
        request.user = make_user(role=Role.TEACHER)

        self.assertEqual(view(request).content, b'ok')


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_profile_shows_the_users_details(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casey Rivera')
        self.assertContains(response, 'casey@example.com')

    def test_profile_requires_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('profile')).status_code, 302)

    def test_profile_can_be_edited(self):
        response = self.client.post(
            reverse('profile_edit'),
            {
                'first_name': 'Casey',
                'last_name': 'Rivera-Stone',
                'email': 'casey@example.com',
                'phone': '+63 917 000 0000',
                'address': '12 Mabini St',
            },
        )
        self.assertRedirects(response, reverse('profile'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'Rivera-Stone')
        self.assertEqual(self.user.phone, '+63 917 000 0000')

    def test_profile_edit_rejects_an_email_owned_by_someone_else(self):
        make_user(username='other', email='taken@example.com')
        response = self.client.post(
            reverse('profile_edit'),
            {
                'first_name': 'Casey',
                'last_name': 'Rivera',
                'email': 'taken@example.com',
                'phone': '',
                'address': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_editing_cannot_change_the_users_role(self):
        self.client.post(
            reverse('profile_edit'),
            {
                'first_name': 'Casey',
                'last_name': 'Rivera',
                'email': 'casey@example.com',
                'phone': '',
                'address': '',
                'role': Role.ADMIN,
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, Role.STUDENT)


class PasswordTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_password_change_updates_the_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('password_change'),
            {
                'old_password': 'cornflower-pylon-83',
                'new_password1': 'driftwood-lantern-11',
                'new_password2': 'driftwood-lantern-11',
            },
        )
        self.assertRedirects(response, reverse('profile'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('driftwood-lantern-11'))

    def test_password_reset_sends_an_email(self):
        from django.core import mail

        response = self.client.post(reverse('password_reset'), {'email': 'casey@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reset', mail.outbox[0].subject.lower())

    def test_password_reset_does_not_leak_unknown_addresses(self):
        from django.core import mail

        response = self.client.post(reverse('password_reset'), {'email': 'nobody@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)


class LogoutTests(TestCase):
    def test_logout_ends_the_session(self):
        self.client.force_login(make_user())
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)


class AccessibilityMarkupTests(TestCase):
    """Guards the accessibility affordances the templates are built around."""

    def test_login_form_labels_every_input(self):
        html = self.client.get(reverse('login')).content.decode()
        self.assertIn('for="id_username"', html)
        self.assertIn('for="id_password"', html)

    def test_invalid_field_is_marked_and_described(self):
        html = self.client.post(
            reverse('register'),
            {'username': '', 'email': 'not-an-email'},
        ).content.decode()
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id_email_error', html)

    def test_password_inputs_allow_managers_and_paste(self):
        html = self.client.get(reverse('login')).content.decode()
        self.assertIn('autocomplete="current-password"', html)
        self.assertNotIn('onpaste', html)

    def test_pages_expose_a_skip_link(self):
        self.assertContains(self.client.get(reverse('login')), 'Skip to main content')


class TemplateCommentTests(TestCase):
    """Django's {# #} is single-line only.

    Spanning one across a newline does not comment anything out - the text
    renders onto the page. This walks every template so the mistake cannot
    come back unnoticed.
    """

    def test_no_multiline_hash_comments(self):
        import re
        from pathlib import Path

        from django.conf import settings

        offenders = []
        for directory in settings.TEMPLATES[0]['DIRS']:
            for path in Path(directory).rglob('*.html'):
                text = path.read_text(encoding='utf-8')
                for match in re.finditer(r'\{#.*?#\}', text, re.DOTALL):
                    if '\n' in match.group(0):
                        line = text.count('\n', 0, match.start()) + 1
                        offenders.append(f'{path.name}:{line}')

        self.assertEqual(
            offenders,
            [],
            'Multi-line {# #} renders as visible text; use {% comment %} instead.',
        )


class UserManagementTests(TestCase):
    """Admin-only user CRUD, bulk actions, and the audit trail they leave."""

    payload = {
        'first_name': 'Dana',
        'last_name': 'Okonkwo',
        'username': 'dana',
        'email': 'dana@example.com',
        'role': Role.TEACHER,
        'phone': '555-0100',
        'address': '',
        'is_active': 'on',
        'password1': 'cornflower-pylon-83',
        'password2': 'cornflower-pylon-83',
    }

    def setUp(self):
        self.admin = make_user('amy-admin', Role.ADMIN)
        self.client.force_login(self.admin)

    def test_students_cannot_reach_user_management(self):
        self.client.force_login(make_user())
        response = self.client.get(reverse('user_list'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_user_list_shows_accounts(self):
        make_user('sam')
        response = self.client.get(reverse('user_list'))
        self.assertContains(response, 'sam')

    def test_user_list_filters_by_role(self):
        make_user('sam')
        make_user('tina', Role.TEACHER)
        response = self.client.get(reverse('user_list'), {'role': Role.TEACHER})
        self.assertNotContains(response, 'sam')
        self.assertContains(response, 'tina')

    def test_creating_a_user_logs_an_entry(self):
        response = self.client.post(reverse('user_create'), self.payload)
        self.assertEqual(response.status_code, 302)

        dana = User.objects.get(username='dana')
        self.assertEqual(dana.role, Role.TEACHER)
        self.assertTrue(dana.check_password('cornflower-pylon-83'))
        self.assertTrue(dana.is_active)

        from apps.reports.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(action='user.created').exists())

    def test_creating_an_admin_role_is_allowed(self):
        response = self.client.post(reverse('user_create'), {**self.payload, 'role': Role.ADMIN})
        self.assertRedirects(response, reverse('user_detail', kwargs={'pk': User.objects.get(username='dana').pk}))

    def test_editing_keeps_password_when_field_is_blank(self):
        sam = make_user('sam')
        response = self.client.post(
            reverse('user_edit', kwargs={'pk': sam.pk}),
            {
                'first_name': 'Samantha',
                'last_name': 'Rivera',
                'username': 'sam',
                'email': 'sam@example.com',
                'role': Role.STUDENT,
                'phone': '',
                'address': '',
                'is_active': 'on',
                'password': '',
            },
        )
        self.assertRedirects(response, reverse('user_detail', kwargs={'pk': sam.pk}))
        sam.refresh_from_db()
        self.assertEqual(sam.first_name, 'Samantha')
        self.assertTrue(sam.check_password('cornflower-pylon-83'))

    def test_editing_can_supply_a_new_password(self):
        sam = make_user('sam')
        self.client.post(
            reverse('user_edit', kwargs={'pk': sam.pk}),
            {
                'first_name': 'Sam',
                'last_name': 'Rivera',
                'username': 'sam',
                'email': 'sam@example.com',
                'role': Role.STUDENT,
                'phone': '',
                'address': '',
                'is_active': 'on',
                'password': 'jackdaw-sunset-45',
            },
        )
        sam.refresh_from_db()
        self.assertTrue(sam.check_password('jackdaw-sunset-45'))

    def test_self_delete_is_blocked(self):
        response = self.client.get(reverse('user_delete', kwargs={'pk': self.admin.pk}))
        self.assertRedirects(response, reverse('user_detail', kwargs={'pk': self.admin.pk}))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_delete_removes_the_account(self):
        sam = make_user('sam')
        response = self.client.post(reverse('user_delete', kwargs={'pk': sam.pk}))
        self.assertRedirects(response, reverse('user_list'))
        self.assertFalse(User.objects.filter(pk=sam.pk).exists())

    def test_bulk_deactivate(self):
        sam = make_user('sam')
        self.client.post(
            reverse('user_list'),
            {'action': 'deactivate', 'selected': [str(sam.pk)]},
        )
        sam.refresh_from_db()
        self.assertFalse(sam.is_active)

    def test_bulk_delete_skips_yourself(self):
        sam = make_user('sam')
        self.client.post(
            reverse('user_list'),
            {'action': 'delete', 'selected': [str(sam.pk), str(self.admin.pk)]},
        )
        self.assertFalse(User.objects.filter(pk=sam.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
