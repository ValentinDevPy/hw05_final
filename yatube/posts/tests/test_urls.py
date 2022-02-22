import http

from django.test import TestCase, Client

from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.post.author)

    def test_all_urls_use_correct_template(self):
        """Тестируем используемые страницами шаблоны.Для этого используем
        учётку автора поста, чтобы проверить сразу все страницы.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_all_urls_return_correct_response(self):
        """Тестируем коды ответа, возвращаемые страницами."""
        addresses_response_codes = {
            '/': http.HTTPStatus.OK,
            f'/group/{self.group.slug}/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/': http.HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': http.HTTPStatus.OK,
            '/create/': http.HTTPStatus.OK,
            '/non_existing_page/': http.HTTPStatus.NOT_FOUND,
        }
        for address, response_code in addresses_response_codes.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertEqual(response.status_code, response_code)

    def test_post_edit_correct_responses(self):
        """Тестируем, что страница редактирования поста
        корректно работает для автора и не автора поста.
        """
        author = self.post_author
        not_author = self.authorized_client
        different_templates_of_edit_url = {
            author: http.HTTPStatus.OK,
            not_author: http.HTTPStatus.FOUND,
        }
        for user_type, response_code in (
                different_templates_of_edit_url.items()
        ):
            with self.subTest(user_type=user_type):
                response = user_type.get(f'/posts/{self.post.id}/edit/')
                self.assertEqual(response.status_code, response_code)

    def test_post_create_correct_responses(self):
        """Тестируем, что страница создания поста
        корректно работает для авторизованного и неавторизованного
        пользователей.
        """
        authorized = self.authorized_client
        not_authorized = self.guest_client
        different_templates_of_edit_url = {
            authorized: http.HTTPStatus.OK,
            not_authorized: http.HTTPStatus.FOUND,
        }
        for user_type, response_code in (
                different_templates_of_edit_url.items()
        ):
            with self.subTest(user_type=user_type):
                response = user_type.get('/create/')
                self.assertEqual(response.status_code, response_code)
