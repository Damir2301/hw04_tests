from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовая заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
            id=1,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for url, template, in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_guest(self):
        """Страницы главная, группы, профиль и детальная информация о посте
         доступны неавторизованному клиенту"""
        url_names = {
            '/',
            '/group/test-slug/',
            '/profile/TestUser/',
            '/posts/1/',
        }
        for url in url_names:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_and_post_edit_for_authorized(self):
        """Страницы create и post_edit недоступны неавторизованному клиенту"""
        url_names = {
            '/create/',
            '/posts/1/edit/',
        }
        for url in url_names:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_redirect_guest(self):
        """Страница /create/ перенаправляет неавторизованного клиента
        на страницу авторизации."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_guest(self):
        """Страница posts/post_id/edit/ перенаправляет
         неавторизованного клиента на страницу авторизации."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/')

    def test_wrong_uri_returns_404(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
