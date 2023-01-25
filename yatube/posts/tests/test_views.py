from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_other = User.objects.create_user(username='NotStasBasov')
        cls.group = Group.objects.create(
            title='Тестовое наименование группы',
            slug='test_slug_group',
            description='test_description_group',
        )
        cls.post_without_group = Post.objects.create(
            text='Тестовый текст, вне групп',
            author=cls.user_other,
        )
        cls.post_in_group = Post.objects.create(
            text='Тестовый текст, в группе "Тестовое наименование группы"',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        """Создание авторизованного клиента."""
        self.user = PostViewsTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostViewsTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': 2}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': 2}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj'][0]
        if not page_obj.group:
            page_obj = response.context['page_obj'][1]
        text_obj = page_obj.text
        author_obj = page_obj.author.username
        group_obj = page_obj.group.__str__()
        self.assertEqual(text_obj, PostViewsTests.post_in_group.text)
        self.assertEqual(author_obj, PostViewsTests.user.username)
        self.assertEqual(group_obj, PostViewsTests.group.title)

    def test_page_index_list_is_2(self):
        """Удостоверяемся, что на главную страницу автора пришло ожидаемое
        количество постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj'].object_list
        self.assertEqual(len(page_obj), 2)

    def test_page_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': PostViewsTests.group.slug})
        )
        page_obj = response.context['page_obj']
        group = response.context['group']

        group = group.title
        text_obj = page_obj[0].text
        author_obj = page_obj[0].author.username
        group_obj = page_obj[0].group.title
        self.assertEqual(group, PostViewsTests.group.title)
        self.assertEqual(text_obj, PostViewsTests.post_in_group.text)
        self.assertEqual(author_obj, PostViewsTests.user.username)
        self.assertEqual(group_obj, PostViewsTests.group.title)

    def test_page_group_list_list_is_1(self):
        """Удостоверяемся, что на страницу с выбранной группой
        пришло ожидаемое количество постов."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': PostViewsTests.group.slug})
        )
        page_obj = response.context['page_obj'].object_list
        self.assertEqual(len(page_obj), 1)

    def test_page_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': PostViewsTests.user.username
            })
        )
        username = response.context['username']
        page_obj = response.context['page_obj'][0]

        username = username.username
        text_obj = page_obj.text
        author_obj = page_obj.author.username
        group_obj = page_obj.group.__str__()
        self.assertEqual(username, PostViewsTests.user.username)
        self.assertEqual(text_obj, PostViewsTests.post_in_group.text)
        self.assertEqual(author_obj, PostViewsTests.user.username)
        self.assertEqual(group_obj, PostViewsTests.group.title)

    def test_page_profile_list_is_1(self):
        """Удостоверяемся, что на страницу автора пришло ожидаемое количество
         постов."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': PostViewsTests.user_other.username
            })
        )
        page_obj = response.context['page_obj'].object_list
        self.assertEqual(len(page_obj), 1)

    def test_page_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 2})
        )
        page_obj = response.context['post']
        text_obj = page_obj.text
        author_obj = page_obj.author.username
        group_obj = page_obj.group.__str__()
        self.assertEqual(text_obj, PostViewsTests.post_in_group.text)
        self.assertEqual(author_obj, PostViewsTests.user.username)
        self.assertEqual(group_obj, PostViewsTests.group.title)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 2})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        is_edit = response.context['is_edit']
        post_id = response.context['post_id']
        self.assertEqual(is_edit, True)
        self.assertEqual(post_id, 2)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_other = User.objects.create_user(username='NotStasBasov')
        cls.group = Group.objects.create(
            title='Тестовое наименование группы',
            slug='test_slug_group',
            description='test_description_group',
        )
        cls.group_second = Group.objects.create(
            title='Тестовое наименование второй группы',
            slug='test_slug_second_group',
            description='test_description_second_group',
        )
        for i in range(13):
            Post.objects.create(
                text='Пост в группе "Тестовое наименование второй группы"',
                author=cls.user_other,
                group=cls.group_second,
            )
        for i in range(18):
            Post.objects.create(
                text='Тестовый текст, в группе "Тестовое наименование группы"',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        """Создание авторизованного клиента."""
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице index равно 10."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице index равно 10."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_three_page_contains_three_records(self):
        """Проверка: количество постов на четвертой странице index равно 1."""
        response = self.client.get(reverse('posts:index') + '?page=4')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице profile равно 10."""
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTest.user.username})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице profile
        равно 8."""
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTest.user.username}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 8)

    def test_group_list_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице group_list
        равно 10."""
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group_second.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице group_list
        равно 3."""
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group_second.slug}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
