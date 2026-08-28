from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role
from apps.courses.models import Course, Enrollment

from .models import Grade

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


def make_grade(student, course, assignment='Quiz 1', **extra):
    return Grade.objects.create(
        student=student,
        course=course,
        assignment_name=assignment,
        grade=extra.pop('grade', 'A'),
        percentage=extra.pop('percentage', 92),
        **extra,
    )


def enroll(student, course):
    return Enrollment.objects.create(student=student, course=course)


class GradeModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)

    def test_string_representation(self):
        grade = make_grade(self.student, self.course)
        self.assertEqual(
            str(grade), f'{self.student.display_name} - Quiz 1 (A)'
        )

    def test_unique_together_per_assignment(self):
        make_grade(self.student, self.course)
        with self.assertRaises(Exception):
            make_grade(self.student, self.course, assignment='Quiz 1')

    def test_percentage_is_limited_to_100(self):
        grade = make_grade(self.student, self.course, percentage=101)
        with self.assertRaises(ValidationError):
            grade.full_clean()

    def test_pass_flag(self):
        self.assertTrue(make_grade(self.student, self.course, percentage=80).is_pass)
        self.assertFalse(make_grade(self.student, self.course, assignment='Quiz 2', percentage=45).is_pass)


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.grade = make_grade(self.student, self.course)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('grade_list'),
            reverse('grade_add'),
            reverse('grade_report'),
            reverse('grade_edit', args=[self.grade.pk]),
            reverse('grade_delete', args=[self.grade.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class GradeListTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.other_course = make_course(self.other_teacher, code='SCI200', name='Biology')
        self.own_grade = make_grade(self.student, self.course, assignment='Quiz 1')
        self.other_grade = make_grade(self.student, self.other_course, assignment='Quiz 1')

    def test_student_sees_only_their_own_grades(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('grade_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_teacher_sees_grades_only_for_their_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('grade_list'))
        self.assertContains(response, 'MATH101')
        self.assertNotContains(response, 'SCI200')

    def test_admin_sees_every_grade(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('grade_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_course_filter_limits_grades(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('grade_list'), {'course': self.course.pk})
        self.assertContains(response, 'MATH101')
        self.assertNotIn(self.other_grade, response.context['grades'])

    def test_student_does_not_see_edit_controls(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('grade_list'))
        self.assertNotContains(response, 'Add grade')


class GradeAddTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        enroll(self.student, self.course)
        self.payload = {
            'student': self.student.pk,
            'course': self.course.pk,
            'assignment_name': 'Quiz 1',
            'grade': 'A',
            'percentage': 92,
            'comments': '',
        }

    def test_student_cannot_add_grades(self):
        self.client.force_login(make_user('kid', Role.STUDENT))
        response = self.client.get(reverse('grade_add'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_teacher_can_add_a_grade_for_their_student(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('grade_add'), self.payload)
        self.assertRedirects(response, reverse('grade_list'))
        self.assertTrue(
            Grade.objects.filter(student=self.student, course=self.course).exists()
        )

    def test_teacher_cannot_grade_for_someone_elses_course(self):
        other_course = make_course(make_user('tom', Role.TEACHER), code='SCI200')
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('grade_add'), {**self.payload, 'course': other_course.pk})
        self.assertRedirects(response, reverse('grade_list'))
        self.assertFalse(Grade.objects.exists())

    def test_teacher_can_only_choose_enrolled_students(self):
        outsider = make_user('rita', Role.STUDENT)
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('grade_add'), {**self.payload, 'student': outsider.pk})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Grade.objects.exists())


class GradeEditTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        enroll(self.student, self.course)
        self.grade = make_grade(self.student, self.course)

    def test_owning_teacher_can_edit(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('grade_edit', args=[self.grade.pk]),
            {
                'student': self.student.pk,
                'course': self.course.pk,
                'assignment_name': 'Quiz 1',
                'grade': 'B+',
                'percentage': 88,
                'comments': 'Good effort',
            },
        )
        self.assertRedirects(response, reverse('grade_list'))
        self.grade.refresh_from_db()
        self.assertEqual(self.grade.grade, 'B+')
        self.assertEqual(float(self.grade.percentage), 88)

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('grade_edit', args=[self.grade.pk]))
        self.assertRedirects(response, reverse('grade_list'))

    def test_student_is_sent_to_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('grade_edit', args=[self.grade.pk]))
        self.assertRedirects(response, reverse('dashboard'))


class GradeDeleteTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.grade = make_grade(self.student, self.course)

    def test_get_shows_confirmation_without_deleting(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('grade_delete', args=[self.grade.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Grade.objects.filter(pk=self.grade.pk).exists())

    def test_owning_teacher_can_delete(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('grade_delete', args=[self.grade.pk]))
        self.assertRedirects(response, reverse('grade_list'))
        self.assertFalse(Grade.objects.filter(pk=self.grade.pk).exists())

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse('grade_delete', args=[self.grade.pk]))
        self.assertRedirects(response, reverse('grade_list'))
        self.assertTrue(Grade.objects.filter(pk=self.grade.pk).exists())

    def test_student_is_sent_to_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('grade_delete', args=[self.grade.pk]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Grade.objects.filter(pk=self.grade.pk).exists())


class GradeReportTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.other_course = make_course(self.other_teacher, code='SCI200')
        enroll(self.student, self.course)
        make_grade(self.student, self.course, assignment='Quiz 1', percentage=92)
        make_grade(self.student, self.course, assignment='Quiz 2', percentage=55)

    def test_report_aggregates_average_and_pass_rate(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('grade_report'), {'course': self.course.pk})
        stats = response.context['stats']
        self.assertEqual(stats['count'], 2)
        self.assertAlmostEqual(float(stats['average']), 73.5)
        self.assertEqual(response.context['pass_rate'], 50)

    def test_teacher_report_is_scoped_to_their_courses(self):
        make_grade(self.student, self.other_course, assignment='Quiz 1', percentage=70)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('grade_report'))
        self.assertNotEqual(response.context['stats']['count'], 3)

    def test_student_cannot_view_report(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('grade_report'))
        self.assertRedirects(response, reverse('dashboard'))
