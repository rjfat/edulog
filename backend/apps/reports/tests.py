import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import Role
from apps.courses.models import Course, Enrollment

from .audit import log_action
from .models import AuditLog, SchoolSettings

User = get_user_model()


def make_user(username, role=Role.STUDENT, **extra):
    return User.objects.create_user(
        username=username,
        email=extra.pop('email', f'{username}@example.com'),
        password=extra.pop('password', 'cornflower-pylon-83'),
        first_name=extra.pop('first_name', username.title()),
        last_name=extra.pop('last_name', 'Test'),
        role=role,
        **extra,
    )


def make_course(teacher, code='MATH101', name='Algebra I', **extra):
    return Course.objects.create(teacher=teacher, code=code, name=name, **extra)


class AuditLogTests(TestCase):
    def test_log_action_records_actor_and_ip(self):
        admin = make_user('ame', Role.ADMIN)
        request = RequestFactory().get('/reports/')
        request.META['REMOTE_ADDR'] = '203.0.113.7'
        request.user = admin

        log_action('unit.test', 'something happened', request=request)

        entry = AuditLog.objects.get(action='unit.test')
        self.assertEqual(entry.user, admin)
        self.assertEqual(entry.ip_address, '203.0.113.7')
        self.assertEqual(entry.details, 'something happened')

    def test_log_action_keeps_ip_blank_without_a_request(self):
        log_action('unit.test', 'from a task that has no request')
        entry = AuditLog.objects.get(action='unit.test')
        self.assertIsNone(entry.ip_address)
        self.assertIsNone(entry.user)

    def test_actions_are_ordered_newest_first(self):
        log_action('unit.test', 'first')
        log_action('unit.test', 'second')
        entries = list(AuditLog.objects.values_list('details', flat=True))
        self.assertEqual(entries, ['second', 'first'])


class AuditSignalTests(TestCase):
    def test_creating_a_course_is_audited(self):
        admin = make_user('ame', Role.ADMIN)
        teacher = make_user('tina', Role.TEACHER)
        self.client.force_login(admin)
        self.client.post(reverse('course_create'), {
            'code': 'PHY101',
            'name': 'Physics',
            'teacher': teacher.pk,
        })

        self.assertTrue(AuditLog.objects.filter(action='course.created').exists())

    def test_creating_a_user_is_audited(self):
        make_user('sam')
        self.assertTrue(AuditLog.objects.filter(action='user.created').exists())

    def test_logging_in_is_audited(self):
        make_user('sam')
        self.client.post(
            reverse('login'), {'username': 'sam', 'password': 'cornflower-pylon-83'}
        )
        self.assertTrue(AuditLog.objects.filter(action='auth.login').exists())


class SchoolSettingsTests(TestCase):
    def test_load_returns_one_singleton_row(self):
        first = SchoolSettings.load()
        second = SchoolSettings.load()
        self.assertEqual(first.pk, 1)
        self.assertEqual(second.pk, first.pk)
        self.assertEqual(SchoolSettings.objects.count(), 1)

    def test_default_school_name(self):
        self.assertEqual(SchoolSettings.load().school_name, 'EduLog')

    def test_settings_can_be_updated(self):
        settings = SchoolSettings.load()
        settings.school_name = 'Northside High'
        settings.save()
        self.assertEqual(SchoolSettings.load().school_name, 'Northside High')


class ReportPermissionTests(TestCase):
    def test_anonymous_visitor_is_sent_to_login(self):
        response = self.client.get(reverse('report_index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_students_have_no_access(self):
        self.client.force_login(make_user('sam'))
        response = self.client.get(reverse('report_index'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_teacher_and_admin_can_open_reports(self):
        for role in (Role.TEACHER, Role.ADMIN):
            with self.subTest(role=role):
                self.client.force_login(make_user(f'u-{role}', role))
                self.assertEqual(self.client.get(reverse('report_index')).status_code, 200)


class StudentReportTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.admin = make_user('ame', Role.ADMIN)
        self.student = make_user('sam')
        self.course = make_course(self.teacher)
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_csv_export_lists_a_student_grades(self):
        from apps.grades.models import Grade

        Grade.objects.create(
            student=self.student,
            course=self.course,
            assignment_name='Quiz 1',
            grade='A',
            percentage=92,
        )
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse('report_student'), {'student': self.student.pk, 'format': 'csv'}
        )
        self.assertEqual(response['Content-Type'], 'text/csv')
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(rows[0], ['Course', 'Assignment', 'Grade', 'Percentage', 'Comments', 'Date'])
        self.assertEqual(rows[1][0], 'MATH101')
        self.assertEqual(rows[1][2], 'A')


class CourseReportTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('otto', Role.TEACHER)
        self.student = make_user('sam')
        self.own = make_course(self.teacher, code='MATH101')
        self.other = make_course(self.other_teacher, code='ART100', name='Drawing')

    def test_teacher_is_limited_to_his_own_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('report_course'), {'course': self.own.pk})
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_report_on_anothers_course(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('report_course'), {'course': self.other.pk})
        self.assertEqual(response.status_code, 404)

    def test_csv_export_has_header(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse('report_course'), {'course': self.own.pk, 'format': 'csv'}
        )
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(rows[0], ['Student', 'Assignments', 'Average %', 'Highest %', 'Passing', 'Pass rate %'])


class AttendanceReportTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam')
        self.course = make_course(self.teacher)

    def test_csv_export_lists_students(self):
        from datetime import date

        from django.utils import timezone

        from apps.attendance.models import Attendance

        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=timezone.localdate(),
            status=Attendance.STATUS_PRESENT,
        )
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse('report_attendance'), {'course': self.course.pk, 'format': 'csv'}
        )
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(rows[0], ['Student', 'Present', 'Absent', 'Late', 'Total', 'Attendance rate %'])
        self.assertEqual(rows[1][4], '1')
        self.assertEqual(rows[1][5], '100')


class SettingsTests(TestCase):
    def test_students_cannot_open_settings(self):
        self.client.force_login(make_user('sam'))
        self.assertRedirects(self.client.get(reverse('settings')), reverse('dashboard'))

    def test_settings_page_renders_for_admin(self):
        self.client.force_login(make_user('ame', Role.ADMIN))
        self.assertEqual(self.client.get(reverse('settings')).status_code, 200)

    def test_saving_settings_logs_an_entry(self):
        admin = make_user('ame', Role.ADMIN)
        self.client.force_login(admin)
        response = self.client.post(reverse('settings'), {
            'school_name': 'Northside High',
            'academic_year': '2026-2027',
            'term_label': '1st Term',
            'contact_email': 'office@northside.example',
        })
        self.assertRedirects(response, reverse('settings'))
        self.assertEqual(SchoolSettings.load().school_name, 'Northside High')
        entry = AuditLog.objects.get(action='settings.updated')
        self.assertIn('Northside High', entry.details)

    def test_school_name_reaches_the_dashboard(self):
        settings = SchoolSettings.load()
        settings.school_name = 'Northside High'
        settings.save()
        admin = make_user('ame', Role.ADMIN)
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse('dashboard')), 'Northside High')


class AuditLogViewTests(TestCase):
    def test_only_admins_can_view_the_log(self):
        self.client.force_login(make_user('sam'))
        self.assertRedirects(self.client.get(reverse('audit_logs')), reverse('dashboard'))

    def test_admins_see_recorded_activity(self):
        admin = make_user('ame', Role.ADMIN)
        self.client.force_login(admin)
        log_action('unit.test', 'seed activity')
        self.assertContains(self.client.get(reverse('audit_logs')), 'seed activity')