from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role
from apps.courses.models import Course, Enrollment

from .models import Attendance

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


def enroll(student, course):
    return Enrollment.objects.create(student=student, course=course)


class AttendanceModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)

    def test_string_representation(self):
        record = Attendance.objects.create(
            student=self.student, course=self.course, date=date(2026, 8, 28), status='present'
        )
        self.assertEqual(
            str(record), f'{self.student.display_name} - Present on 2026-08-28'
        )

    def test_attendance_is_unique_per_student_course_and_date(self):
        Attendance.objects.create(
            student=self.student, course=self.course, date=date(2026, 8, 28), status='present'
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.student, course=self.course, date=date(2026, 8, 28), status='absent'
            )


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('attendance_list'),
            reverse('attendance_mark'),
            reverse('attendance_report'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class AttendanceListTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.other_course = make_course(self.other_teacher, code='SCI200')
        Attendance.objects.create(student=self.student, course=self.course, date=date(2026, 8, 28), status='present')
        Attendance.objects.create(student=self.student, course=self.other_course, date=date(2026, 8, 28), status='absent')

    def test_student_sees_their_own_records(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('attendance_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_teacher_sees_only_their_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('attendance_list'))
        self.assertContains(response, 'MATH101')
        self.assertNotContains(response, 'SCI200')

    def test_admin_sees_every_record(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('attendance_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_course_filter_limits_records(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('attendance_list'), {'course': self.course.pk})
        self.assertContains(response, 'MATH101')
        self.assertNotIn('SCI200', response.content.decode())


class AttendanceMarkTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.second = make_user('sara', Role.STUDENT)
        self.course = make_course(self.teacher)
        enroll(self.student, self.course)
        enroll(self.second, self.course)

    def test_student_cannot_mark_attendance(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('attendance_mark'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_selecting_a_course_and_date_renders_the_roster(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('attendance_mark'),
            {'course': self.course.pk, 'date': '2026-08-28'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save attendance')

    def test_teacher_can_save_attendance_for_the_whole_class(self):
        self.client.force_login(self.teacher)
        data = {
            'save_attendance': '',
            'course': self.course.pk,
            'date': '2026-08-28',
            'rows-TOTAL_FORMS': '2',
            'rows-INITIAL_FORMS': '0',
            'rows-MIN_NUM_FORMS': '0',
            'rows-MAX_NUM_FORMS': '1000',
            'rows-0-status': 'present',
            'rows-0-notes': '',
            'rows-1-status': 'late',
            'rows-1-notes': 'Traffic',
        }
        response = self.client.post(reverse('attendance_mark'), data)
        self.assertRedirects(response, reverse('attendance_list'))
        self.assertEqual(Attendance.objects.filter(course=self.course, date=date(2026, 8, 28)).count(), 2)
        self.assertIsNotNone(
            Attendance.objects.get(student=self.second, course=self.course, date=date(2026, 8, 28))
        )

    def test_resaving_updates_instead_of_duplicating(self):
        Attendance.objects.create(student=self.student, course=self.course, date=date(2026, 8, 28), status='absent')
        self.client.force_login(self.teacher)
        data = {
            'save_attendance': '',
            'course': self.course.pk,
            'date': '2026-08-28',
            'rows-TOTAL_FORMS': '2',
            'rows-INITIAL_FORMS': '0',
            'rows-MIN_NUM_FORMS': '0',
            'rows-MAX_NUM_FORMS': '1000',
            'rows-0-status': 'present',
            'rows-0-notes': '',
            'rows-1-status': 'present',
            'rows-1-notes': '',
        }
        self.client.post(reverse('attendance_mark'), data)
        records = Attendance.objects.filter(course=self.course, date=date(2026, 8, 28))
        self.assertEqual(records.count(), 2)
        self.assertEqual(records.get(student=self.student).status, 'present')

    def test_other_teacher_cannot_save_attendance(self):
        self.client.force_login(self.other_teacher)
        data = {
            'save_attendance': '',
            'course': self.course.pk,
            'date': '2026-08-28',
            'rows-TOTAL_FORMS': '2',
            'rows-INITIAL_FORMS': '0',
            'rows-MIN_NUM_FORMS': '0',
            'rows-MAX_NUM_FORMS': '1000',
            'rows-0-status': 'present',
            'rows-0-notes': '',
            'rows-1-status': 'present',
            'rows-1-notes': '',
        }
        self.client.post(reverse('attendance_mark'), data)
        self.assertFalse(Attendance.objects.exists())


class AttendanceReportTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.other_course = make_course(self.other_teacher, code='SCI200')
        for day in (1, 2, 3, 4):
            Attendance.objects.create(
                student=self.student, course=self.course,
                date=date(2026, 8, day), status='present',
            )
        Attendance.objects.create(
            student=self.student, course=self.course, date=date(2026, 8, 5), status='absent'
        )

    def test_report_computes_present_rate(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('attendance_report'), {'course': self.course.pk})
        self.assertEqual(response.context['overall']['total'], 5)
        self.assertEqual(response.context['overall']['present_rate'], 80)

    def test_teacher_report_is_scoped_to_their_courses(self):
        Attendance.objects.create(
            student=self.student, course=self.other_course, date=date(2026, 8, 28), status='present'
        )
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('attendance_report'))
        self.assertEqual(response.context['overall']['total'], 5)

    def test_student_cannot_view_report(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('attendance_report'))
        self.assertRedirects(response, reverse('dashboard'))
