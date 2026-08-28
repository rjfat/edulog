from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role

from .models import Announcement

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


def make_announcement(author, title='Midterm schedules', **extra):
    return Announcement.objects.create(
        author=author,
        title=title,
        content=extra.pop('content', 'Please check your class schedules.'),
        **extra,
    )


class AnnouncementModelTests(TestCase):
    def setUp(self):
        self.author = make_user('tia', Role.TEACHER)

    def test_string_representation(self):
        announcement = make_announcement(self.author)
        self.assertEqual(str(announcement), 'Midterm schedules')

    def test_default_target_is_everyone(self):
        announcement = make_announcement(self.author)
        self.assertEqual(announcement.target_role, Announcement.TARGET_ALL)

    def test_newest_first_ordering(self):
        older = make_announcement(self.author, title='Older')
        newer = make_announcement(self.author, title='Newer')
        Announcement.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        Announcement.objects.filter(pk=newer.pk).update(created_at=timezone.now())
        self.assertEqual(
            list(Announcement.objects.values_list('title', flat=True)),
            ['Newer', 'Older'],
        )


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.author = make_user('tia', Role.TEACHER)
        self.announcement = make_announcement(self.author)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('announcement_list'),
            reverse('announcement_create'),
            reverse('announcement_edit', args=[self.announcement.pk]),
            reverse('announcement_delete', args=[self.announcement.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class AnnouncementListTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.student = make_user('sam', Role.STUDENT)
        self.admin = make_user('root', Role.ADMIN)
        self.for_all = make_announcement(self.admin, title='School fair')
        self.for_students = make_announcement(
            self.teacher, title='Quiz tips', target_role=Announcement.TARGET_STUDENT
        )
        self.for_teachers = make_announcement(
            self.teacher, title='Staff meeting', target_role=Announcement.TARGET_TEACHER
        )

    def test_admin_sees_every_announcement(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('announcement_list'))
        self.assertContains(response, 'School fair')
        self.assertContains(response, 'Quiz tips')
        self.assertContains(response, 'Staff meeting')

    def test_student_sees_only_their_own_targeting(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('announcement_list'))
        self.assertContains(response, 'School fair')
        self.assertContains(response, 'Quiz tips')
        self.assertNotContains(response, 'Staff meeting')

    def test_teacher_sees_their_own_posts_even_when_targeted_at_students(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('announcement_list'))
        self.assertContains(response, 'Quiz tips')

    def test_student_does_not_see_management_controls(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('announcement_list'))
        self.assertNotContains(response, 'New announcement')


class AnnouncementCreateTests(TestCase):
    def test_students_cannot_create_announcements(self):
        self.client.force_login(make_user('sam', Role.STUDENT))
        response = self.client.get(reverse('announcement_create'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_teacher_can_post_and_is_recorded_as_author(self):
        teacher = make_user('tina', Role.TEACHER)
        self.client.force_login(teacher)
        response = self.client.post(
            reverse('announcement_create'),
            {'title': 'Homework help', 'content': 'Ask in class.', 'target_role': 'student'},
        )
        self.assertRedirects(response, reverse('announcement_list'))
        announcement = Announcement.objects.get(title='Homework help')
        self.assertEqual(announcement.author, teacher)

    def test_teacher_cannot_target_parents(self):
        self.client.force_login(make_user('tina', Role.TEACHER))
        response = self.client.post(
            reverse('announcement_create'),
            {'title': 'To parents', 'content': 'Hi', 'target_role': 'parent'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Announcement.objects.filter(title='To parents').exists())

    def test_admin_can_target_any_role(self):
        admin = make_user('root', Role.ADMIN)
        self.client.force_login(admin)
        response = self.client.post(
            reverse('announcement_create'),
            {'title': 'Parent night', 'content': 'Join us.', 'target_role': 'parent'},
        )
        self.assertRedirects(response, reverse('announcement_list'))
        self.assertEqual(Announcement.objects.get(title='Parent night').target_role, 'parent')


class AnnouncementEditTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.announcement = make_announcement(self.teacher, title='Field trip')

    def test_author_can_edit(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('announcement_edit', args=[self.announcement.pk]),
            {'title': 'Field trip (moved)', 'content': 'New date.', 'target_role': 'all'},
        )
        self.assertRedirects(response, reverse('announcement_list'))
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, 'Field trip (moved)')

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse('announcement_edit', args=[self.announcement.pk]))
        self.assertRedirects(response, reverse('announcement_list'))

    def test_admin_can_edit_any_announcement(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(
            reverse('announcement_edit', args=[self.announcement.pk]),
            {'title': 'Updated by admin', 'content': 'x', 'target_role': 'all'},
        )
        self.assertRedirects(response, reverse('announcement_list'))
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, 'Updated by admin')

    def test_student_is_sent_to_dashboard(self):
        self.client.force_login(make_user('sam', Role.STUDENT))
        response = self.client.get(reverse('announcement_edit', args=[self.announcement.pk]))
        self.assertRedirects(response, reverse('dashboard'))


class AnnouncementDeleteTests(TestCase):
    def setUp(self):
        self.teacher = make_user('tina', Role.TEACHER)
        self.other_teacher = make_user('tom', Role.TEACHER)
        self.announcement = make_announcement(self.teacher)

    def test_get_shows_confirmation_without_deleting(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('announcement_delete', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete announcement')
        self.assertTrue(Announcement.objects.filter(pk=self.announcement.pk).exists())

    def test_author_can_delete(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('announcement_delete', args=[self.announcement.pk]))
        self.assertRedirects(response, reverse('announcement_list'))
        self.assertFalse(Announcement.objects.filter(pk=self.announcement.pk).exists())

    def test_other_teacher_is_denied(self):
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse('announcement_delete', args=[self.announcement.pk]))
        self.assertRedirects(response, reverse('announcement_list'))
        self.assertTrue(Announcement.objects.filter(pk=self.announcement.pk).exists())

    def test_admin_can_delete(self):
        self.client.force_login(make_user('root', Role.ADMIN))
        response = self.client.post(reverse('announcement_delete', args=[self.announcement.pk]))
        self.assertRedirects(response, reverse('announcement_list'))
        self.assertFalse(Announcement.objects.filter(pk=self.announcement.pk).exists())