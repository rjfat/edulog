from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role
from apps.courses.models import Course, Enrollment

from .models import Schedule

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


def make_schedule(course, day=Schedule.MONDAY, **extra):
    return Schedule.objects.create(
        course=course,
        day_of_week=day,
        start_time=extra.pop('start_time', time(8, 0)),
        end_time=extra.pop('end_time', time(9, 0)),
        room=extra.pop('room', 'Room 12'),
        **extra,
    )


def enroll(student, course):
    return Enrollment.objects.create(student=student, course=course)


class ScheduleModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)

    def test_string_representation(self):
        schedule = make_schedule(self.course, start_time=time(8, 30))
        self.assertEqual(str(schedule), 'MATH101 Monday 08:30')

    def test_slots_order_by_day_then_time(self):
        make_schedule(self.course, day=Schedule.TUESDAY, start_time=time(9, 0))
        make_schedule(self.course, day=Schedule.MONDAY, start_time=time(11, 0))
        make_schedule(self.course, day=Schedule.MONDAY, start_time=time(8, 0))
        self.assertEqual(
            list(Schedule.objects.values_list('start_time', flat=True)),
            [time(8, 0), time(11, 0), time(9, 0)],
        )


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.course = make_course(self.teacher)
        self.schedule = make_schedule(self.course)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('timetable'),
            reverse('schedule_create'),
            reverse('schedule_edit', args=[self.schedule.pk]),
            reverse('schedule_delete', args=[self.schedule.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class TimetableTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.own_course = make_course(self.teacher, code='MATH101')
        self.other_course = make_course(self.other_teacher, code='SCI200')
        self.own_session = make_schedule(self.own_course, day=Schedule.MONDAY)
        make_schedule(self.other_course, day=Schedule.TUESDAY)

    def test_monday_column_is_first(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('timetable'))
        first_day = response.context['days'][0]
        self.assertEqual(first_day['day'], Schedule.MONDAY)
        self.assertEqual(first_day['label'], 'Monday')

    def test_teacher_sees_only_their_own_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('timetable'))
        self.assertContains(response, 'MATH101')
        self.assertNotContains(response, 'SCI200')

    def test_student_sees_only_enrolled_courses(self):
        enroll(self.student, self.own_course)
        self.client.force_login(self.student)
        response = self.client.get(reverse('timetable'))
        self.assertContains(response, 'MATH101')
        self.assertNotContains(response, 'SCI200')

    def test_admin_sees_every_course(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.get(reverse('timetable'))
        self.assertContains(response, 'MATH101')
        self.assertContains(response, 'SCI200')

    def test_student_gets_no_management_controls(self):
        enroll(self.student, self.own_course)
        self.client.force_login(self.student)
        response = self.client.get(reverse('timetable'))
        self.assertNotContains(response, 'Add class')

    def test_empty_timetable_shows_an_empty_state(self):
        self.client.force_login(make_user('solo', Role.STUDENT))
        response = self.client.get(reverse('timetable'))
        self.assertContains(response, 'No classes have been scheduled')


class ScheduleCreateEditDeleteTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.course = make_course(self.teacher)
        self.other_course = make_course(self.other_teacher, code='SCI200')
        self.payload = {
            'course': self.course.pk,
            'day_of_week': Schedule.TUESDAY,
            'start_time': '13:00',
            'end_time': '14:30',
            'room': 'Lab 3',
        }

    def test_student_cannot_create_schedule_slots(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('schedule_create'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_teacher_can_schedule_one_of_their_own_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('schedule_create'), self.payload)
        self.assertRedirects(response, reverse('timetable'))
        schedule = Schedule.objects.get(course=self.course)
        self.assertEqual(schedule.day_of_week, Schedule.TUESDAY)
        self.assertEqual(schedule.room, 'Lab 3')

    def test_teacher_cannot_schedule_someone_elses_course(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('schedule_create'), {**self.payload, 'course': self.other_course.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Schedule.objects.exists())

    def test_admin_can_schedule_any_course(self):
        admin = make_user('root', Role.ADMIN)
        self.client.force_login(admin)
        response = self.client.post(
            reverse('schedule_create'), {**self.payload, 'course': self.other_course.pk}
        )
        self.assertRedirects(response, reverse('timetable'))
        self.assertTrue(Schedule.objects.filter(course=self.other_course).exists())

    def test_owning_teacher_can_edit_the_slot(self):
        schedule = make_schedule(self.course)
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('schedule_edit', args=[schedule.pk]),
            {**self.payload, 'day_of_week': Schedule.FRIDAY, 'room': 'Hall A'},
        )
        self.assertRedirects(response, reverse('timetable'))
        schedule.refresh_from_db()
        self.assertEqual(schedule.day_of_week, Schedule.FRIDAY)
        self.assertEqual(schedule.room, 'Hall A')

    def test_other_teacher_cannot_edit_the_slot(self):
        schedule = make_schedule(self.course)
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('schedule_edit', args=[schedule.pk]))
        self.assertRedirects(response, reverse('timetable'))

    def test_owning_teacher_can_remove_the_slot(self):
        schedule = make_schedule(self.course)
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('schedule_delete', args=[schedule.pk]))
        self.assertRedirects(response, reverse('timetable'))
        self.assertFalse(Schedule.objects.filter(pk=schedule.pk).exists())

    def test_other_teacher_cannot_remove_the_slot(self):
        schedule = make_schedule(self.course)
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse('schedule_delete', args=[schedule.pk]))
        self.assertRedirects(response, reverse('timetable'))
        self.assertTrue(Schedule.objects.filter(pk=schedule.pk).exists())