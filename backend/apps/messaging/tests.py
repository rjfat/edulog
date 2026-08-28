from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role

from .models import Message

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


def make_message(sender, receiver, subject='Hello', **extra):
    return Message.objects.create(
        sender=sender,
        receiver=receiver,
        subject=subject,
        body=extra.pop('body', 'Just checking in.'),
        **extra,
    )


class MessageModelTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)

    def test_string_representation(self):
        message = make_message(self.sender, self.receiver)
        self.assertEqual(
            str(message),
            f'{self.sender.display_name} → {self.receiver.display_name}: Hello',
        )

    def test_new_messages_start_unread(self):
        message = make_message(self.sender, self.receiver)
        self.assertFalse(message.read)

    def test_newest_first_ordering(self):
        older = make_message(self.sender, self.receiver, subject='Older')
        newer = make_message(self.sender, self.receiver, subject='Newer')
        Message.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        Message.objects.filter(pk=newer.pk).update(created_at=timezone.now())
        self.assertEqual(
            list(Message.objects.values_list('subject', flat=True)),
            ['Newer', 'Older'],
        )


class AnonymousAccessTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)
        self.message = make_message(self.sender, self.receiver)

    def test_every_view_redirects_anonymous_visitors_to_login(self):
        urls = [
            reverse('message_inbox'),
            reverse('message_sent'),
            reverse('message_compose'),
            reverse('message_detail', args=[self.message.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)


class InboxSentTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)
        self.incoming = make_message(self.sender, self.receiver, subject='Homework')
        self.outgoing = make_message(self.receiver, self.sender, subject='Question')

    def test_inbox_only_lists_received_messages(self):
        self.client.force_login(self.receiver)
        response = self.client.get(reverse('message_inbox'))
        self.assertContains(response, 'Homework')
        self.assertNotContains(response, 'Question')

    def test_sent_only_lists_sent_messages(self):
        self.client.force_login(self.receiver)
        response = self.client.get(reverse('message_sent'))
        self.assertContains(response, 'Question')
        self.assertNotContains(response, 'Homework')


class ComposeTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)

    def test_any_authenticated_user_can_send(self):
        self.client.force_login(self.sender)
        response = self.client.post(
            reverse('message_compose'),
            {'receiver': self.receiver.pk, 'subject': 'Reminder', 'body': 'Be on time.'},
        )
        self.assertRedirects(response, reverse('message_sent'))
        message = Message.objects.get(subject='Reminder')
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)

    def test_you_cannot_message_yourself(self):
        self.client.force_login(self.sender)
        response = self.client.post(
            reverse('message_compose'),
            {'receiver': self.sender.pk, 'subject': 'To me', 'body': 'x'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Message.objects.filter(subject='To me').exists())

    def test_receiver_options_exclude_yourself(self):
        self.client.force_login(self.sender)
        response = self.client.get(reverse('message_compose'))
        queryset = response.context['form'].fields['receiver'].queryset
        self.assertIn(self.receiver, queryset)
        self.assertNotIn(self.sender, queryset)

    def test_reply_to_prefills_the_receiver(self):
        self.client.force_login(self.receiver)
        response = self.client.get(reverse('message_compose'), {'to': self.sender.pk})
        self.assertEqual(
            response.context['form'].initial['receiver'], str(self.sender.pk)
        )


class MessageDetailTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)
        self.other = make_user('rita', Role.STUDENT)
        self.message = make_message(self.sender, self.receiver)

    def test_receiver_viewing_marks_the_message_read(self):
        self.client.force_login(self.receiver)
        self.client.get(reverse('message_detail', args=[self.message.pk]))
        self.message.refresh_from_db()
        self.assertTrue(self.message.read)

    def test_sender_viewing_does_not_touch_the_read_flag(self):
        self.client.force_login(self.sender)
        self.client.get(reverse('message_detail', args=[self.message.pk]))
        self.message.refresh_from_db()
        self.assertFalse(self.message.read)

    def test_unrelated_user_is_denied(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('message_detail', args=[self.message.pk]))
        self.assertRedirects(response, reverse('message_inbox'))

    def test_recipient_sees_a_reply_button(self):
        self.client.force_login(self.receiver)
        response = self.client.get(reverse('message_detail', args=[self.message.pk]))
        self.assertContains(response, 'Reply')


class UnreadCountTests(TestCase):
    def setUp(self):
        self.sender = make_user('tina', Role.TEACHER)
        self.receiver = make_user('sam', Role.STUDENT)

    def test_context_processor_counts_unread_mail(self):
        make_message(self.sender, self.receiver)
        make_message(self.sender, self.receiver, subject='Read me', read=True)
        make_message(self.sender, self.receiver, subject='Unread two')
        self.client.force_login(self.receiver)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['unread_message_count'], 2)

    def test_unread_is_zero_for_anonymous_visitors(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.context['unread_message_count'], 0)