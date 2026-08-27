from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role

from .models import Course, Enrollment

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


class CourseModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)

    def test_string_representation(self):
        course = make_course(self.teacher)
        self.assertEqual(str(course), 'MATH101 - Algebra I')

    def test_courses_are_ordered_by_code(self):
        make_course(self.teacher, code='SCI200', name='Biology')
        make_course(self.teacher, code='ART100', name='Drawing')
        self.assertEqual(list(Course.objects.values_list('code', flat=True)), ['ART100', 'SCI200'])

    def test_code_must_be_unique(self):
        make_course(self.teacher, code='MATH101')
        with self.assertRaises(Exception):
            make_course(self.teacher, code='MATH101', name='Algebra II')


class EnrollmentModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)

    def test_string_representation(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.assertEqual(str(enrollment), f'{self.student.display_name} → {self.course.code}')

    def test_a_student_cannot_double_enroll(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.student, course=self.course)


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('course_list'),
            reverse('course_create'),
            reverse('course_detail', args=[self.course.pk]),
            reverse('course_edit', args=[self.course.pk]),
            reverse('course_delete', args=[self.course.pk]),
            reverse('course_roster', args=[self.course.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class CourseListTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.own_course = make_course(self.teacher, code='MATH101', name='Algebra I')
        self.other_course = make_course(self.other_teacher, code='SCI200', name='Biology')

    def test_admin_sees_every_course(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('course_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_teacher_sees_only_their_own_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('course_list'))
        self.assertContains(response, 'MATH101')
        self.assertNotContains(response, 'SCI200')

    def test_student_sees_every_course_with_enrollment_status(self):
        Enrollment.objects.create(student=self.student, course=self.own_course)
        self.client.force_login(self.student)
        response = self.client.get(reverse('course_list'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')
        self.assertContains(response, 'Enrolled')

    def test_new_course_button_is_hidden_from_students(self):
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse('course_list')), 'New course')

    def test_new_course_button_is_shown_to_teachers(self):
        self.client.force_login(self.teacher)
        self.assertContains(self.client.get(reverse('course_list')), 'New course')


class CourseCreateTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.payload = {'name': 'Algebra I', 'code': 'MATH101', 'description': 'Intro algebra'}

    def test_students_cannot_create_courses(self):
        self.client.force_login(make_user('sam', Role.STUDENT))
        self.assertRedirects(self.client.get(reverse('course_create')), reverse('dashboard'))

    def test_teacher_creating_a_course_is_assigned_as_its_teacher(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('course_create'), self.payload)
        course = Course.objects.get(code='MATH101')
        self.assertRedirects(response, reverse('course_detail', args=[course.pk]))
        self.assertEqual(course.teacher, self.teacher)

    def test_teacher_cannot_pick_a_different_teacher(self):
        other = make_user('tom', Role.TEACHER)
        self.client.force_login(self.teacher)
        self.client.post(reverse('course_create'), {**self.payload, 'teacher': other.pk})
        self.assertEqual(Course.objects.get(code='MATH101').teacher, self.teacher)

    def test_admin_must_choose_a_teacher(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(reverse('course_create'), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(code='MATH101').exists())

    def test_admin_can_assign_any_teacher(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(reverse('course_create'), {**self.payload, 'teacher': self.teacher.pk})
        course = Course.objects.get(code='MATH101')
        self.assertRedirects(response, reverse('course_detail', args=[course.pk]))
        self.assertEqual(course.teacher, self.teacher)

    def test_duplicate_code_is_rejected(self):
        make_course(self.teacher, code='MATH101')
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('course_create'), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')


class CourseDetailTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)

    def test_owning_teacher_can_manage(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertTrue(response.context['can_manage'])
        self.assertContains(response, 'Manage roster')

    def test_other_teacher_cannot_manage(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertFalse(response.context['can_manage'])
        self.assertNotContains(response, 'Manage roster')

    def test_admin_can_always_manage(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertTrue(response.context['can_manage'])

    def test_delete_button_is_admin_only(self):
        self.client.force_login(self.teacher)
        self.assertNotContains(
            self.client.get(reverse('course_detail', args=[self.course.pk])), 'Delete'
        )

    def test_student_sees_enroll_button_when_not_enrolled(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertFalse(response.context['is_enrolled'])
        self.assertContains(response, 'Enroll')

    def test_enrolled_student_sees_leave_button(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.student)
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertTrue(response.context['is_enrolled'])
        self.assertContains(response, 'Leave course')


class CourseEditTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.course = make_course(self.teacher)

    def test_owning_teacher_can_edit(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('course_edit', args=[self.course.pk]),
            {'name': 'Algebra I (Updated)', 'code': 'MATH101', 'description': ''},
        )
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Algebra I (Updated)')

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('course_edit', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))

    def test_student_is_sent_to_the_dashboard(self):
        self.client.force_login(make_user('sam', Role.STUDENT))
        response = self.client.get(reverse('course_edit', args=[self.course.pk]))
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_can_reassign_the_teacher(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(
            reverse('course_edit', args=[self.course.pk]),
            {
                'name': self.course.name,
                'code': self.course.code,
                'description': '',
                'teacher': self.other_teacher.pk,
            },
        )
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.course.refresh_from_db()
        self.assertEqual(self.course.teacher, self.other_teacher)


class CourseDeleteTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)

    def test_teacher_cannot_delete(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('course_delete', args=[self.course.pk]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_get_shows_a_confirmation_page_without_deleting(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('course_delete', args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete course')
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_admin_can_delete(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(reverse('course_delete', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_list'))
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())

    def test_deleting_a_course_removes_its_enrollments(self):
        student = make_user('sam', Role.STUDENT)
        Enrollment.objects.create(student=student, course=self.course)
        self.client.force_login(make_user('root', Role.ADMIN))
        self.client.post(reverse('course_delete', args=[self.course.pk]))
        self.assertFalse(Enrollment.objects.filter(course_id=self.course.pk).exists())


class RosterTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.course = make_course(self.teacher)
        self.student = make_user('sam', Role.STUDENT)
        self.other_student = make_user('sara', Role.STUDENT)

    def test_owning_teacher_sees_the_roster(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('course_roster', args=[self.course.pk]))
        self.assertContains(response, self.student.display_name)

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('course_roster', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))

    def test_student_is_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('course_roster', args=[self.course.pk]))
        self.assertRedirects(response, reverse('dashboard'))

    def test_enrollment_form_excludes_already_enrolled_students(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('course_roster', args=[self.course.pk]))
        queryset = response.context['form'].fields['student'].queryset
        self.assertNotIn(self.student, queryset)
        self.assertIn(self.other_student, queryset)

    def test_enrollment_form_only_offers_students(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('course_roster', args=[self.course.pk]))
        queryset = response.context['form'].fields['student'].queryset
        self.assertNotIn(self.other_teacher, queryset)

    def test_teacher_can_enroll_a_student(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('course_enroll', args=[self.course.pk]), {'student': self.student.pk}
        )
        self.assertRedirects(response, reverse('course_roster', args=[self.course.pk]))
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_other_teacher_cannot_enroll_a_student(self):
        self.client.force_login(self.other_teacher)
        self.client.post(reverse('course_enroll', args=[self.course.pk]), {'student': self.student.pk})
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_enrolling_without_a_student_shows_an_error(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('course_enroll', args=[self.course.pk]), {}, follow=True)
        self.assertContains(response, 'Choose a student to enroll.')

    def test_teacher_can_remove_a_student(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('course_unenroll', args=[self.course.pk, self.student.pk])
        )
        self.assertRedirects(response, reverse('course_roster', args=[self.course.pk]))
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_other_teacher_cannot_remove_a_student(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.other_teacher)
        self.client.post(reverse('course_unenroll', args=[self.course.pk, self.student.pk]))
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())


class SelfServiceEnrollmentTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)
        self.student = make_user('sam', Role.STUDENT)

    def test_student_can_join(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('course_join', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_joining_twice_does_not_duplicate_the_enrollment(self):
        self.client.force_login(self.student)
        self.client.post(reverse('course_join', args=[self.course.pk]))
        self.client.post(reverse('course_join', args=[self.course.pk]))
        self.assertEqual(
            Enrollment.objects.filter(student=self.student, course=self.course).count(), 1
        )

    def test_student_can_leave(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.student)
        response = self.client.post(reverse('course_leave', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_leaving_when_not_enrolled_is_a_no_op(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('course_leave', args=[self.course.pk]))
        self.assertEqual(response.status_code, 302)

    def test_teachers_cannot_self_join(self):
        other_teacher = make_user('tom', Role.TEACHER)
        self.client.force_login(other_teacher)
        response = self.client.get(reverse('course_join', args=[self.course.pk]))
        self.assertRedirects(response, reverse('dashboard'))

    def test_admins_cannot_self_join(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('course_join', args=[self.course.pk]))
        self.assertRedirects(response, reverse('dashboard'))
