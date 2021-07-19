from http import HTTPStatus
import logging
from unittest.mock import patch

from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import OperationalError
from django.test import Client, TestCase
from django.urls import reverse

from core.models import User

ADMIN_URL = reverse("admin:index")
ADMIN_LOGIN_URL = reverse("admin:login")


def get_test_user(
    username="testuser", email="testuser@email.com", **kwargs
) -> User:
    password = kwargs.get("password", "password")
    return User.objects.create(
        username=username, email=email, password=password, **kwargs
    )


def get_staff_user(
    username="staffuser", email="staffuser@email.com", **kwargs
) -> User:
    return get_test_user(username, email, is_staff=True, **kwargs)


def get_super_user(
    username="superuser", email="superuser@email.com", **kwargs
) -> User:
    return get_staff_user(username, email, is_superuser=True, **kwargs)


def suppress_logs(original_function, loglevel="ERROR"):
    def new_function(*args, **kwargs):
        """wrap original_function with suppressed warnings"""
        # raise logging level to ERROR or loglevel
        logger = logging.getLogger("django")
        previous_logging_level = logger.getEffectiveLevel()
        logger.setLevel(getattr(logging, loglevel.upper()))

        # trigger original function that would throw warning
        original_function(*args, **kwargs)

        # lower logging level back to previous
        logger.setLevel(previous_logging_level)

    return new_function


class CommandsTestCase(TestCase):
    def test_wait_for_db_ready(self) -> None:
        with patch("django.db.utils.ConnectionHandler.__getitem__") as gi:
            gi.return_value = True
            call_command("wait_for_db")
            self.assertEqual(gi.call_count, 1)

    @patch("time.sleep", return_value=None)
    def test_wait_for_db(self, _) -> None:
        with patch("django.db.utils.ConnectionHandler.__getitem__") as gi:
            gi.side_effect = [OperationalError] * 5 + [True]
            call_command("wait_for_db")
            self.assertEqual(gi.call_count, 6)


class AdminTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_test_user()
        self.staffuser = get_staff_user()
        self.superuser = get_super_user()

    def test_redirect_anon_user(self):
        res = self.client.get(ADMIN_URL, follow=True)
        self.assertRedirects(
            response=res,
            expected_url=f"{ADMIN_LOGIN_URL}?next={ADMIN_URL}",
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_redirect_norm_user(self):
        self.client.force_login(user=self.user)
        res = self.client.get(ADMIN_URL, follow=True)
        self.assertRedirects(
            response=res,
            expected_url=f"{ADMIN_LOGIN_URL}?next={ADMIN_URL}",
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        self.client.logout()  # clear session and cookies

    def test_staff_user_access(self):
        self.client.force_login(user=self.staffuser)
        res = self.client.get(ADMIN_URL, follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.wsgi_request.user, self.staffuser)
        self.client.logout()  # clear session and cookies


class LogEntryTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.superuser = get_super_user()
        self.staffuser = get_staff_user()
        self.entry = LogEntry.objects.create(
            user=self.superuser,
            action_flag=ADDITION,
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.staffuser.id,
        )

    def test_staff_view_perms(self):
        self.client.force_login(user=self.staffuser)
        res = self.client.get(
            reverse("admin:admin_logentry_changelist"), follow=True
        )
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.client.logout()  # clear session and cookies

    @suppress_logs  # suppress the PermissionDenied exception
    def test_staff_add_perms(self):
        self.client.force_login(user=self.staffuser)
        res = self.client.get(reverse("admin:admin_logentry_add"), follow=True)
        self.assertEqual(res.status_code, HTTPStatus.FORBIDDEN)
        self.client.logout()  # clear session and cookies

    def test_staff_change_perms(self):
        self.client.force_login(user=self.staffuser)
        res = self.client.get(
            reverse("admin:admin_logentry_change", args=[self.entry.pk]),
            follow=True,
        )
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertContains(
            res, "You don’t have permission to view or edit anything."
        )
        self.client.logout()  # clear session and cookies

    @suppress_logs  # suppress the PermissionDenied exception
    def test_staff_delete_perms(self):
        self.client.force_login(user=self.staffuser)
        res = self.client.get(
            reverse("admin:admin_logentry_delete", args=[self.entry.pk]),
            follow=True,
        )
        self.assertEqual(res.status_code, HTTPStatus.FORBIDDEN)
        self.client.logout()  # clear session and cookies
