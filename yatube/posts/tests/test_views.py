from itertools import islice
import tempfile
import shutil

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User, Comment, Follow
from ..views import (POSTS_ON_INDEX_PAGE,
                     POSTS_ON_GROUP_POSTS_PAGE,
                     POSTS_ON_PROFILE_PAGE,
                     )

NUMBER_OF_POSTS_FROM_AUTHOR_WITH_FIRST_GROUP = 13
NUMBER_OF_ALL_CREATED_POSTS = 14
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.first_group = Group.objects.create(
            title='Тестовый заголовок 1',
            description='Тестовый текст 1',
            slug='test-slug',
        )
        cls.second_group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='another_test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.posts = (Post(
            text=f'Тестовый текст {i}',
            author=cls.author,
            group=cls.first_group,
        )
            for i in range(NUMBER_OF_POSTS_FROM_AUTHOR_WITH_FIRST_GROUP)
        )
        cls.batch = list(islice(
            cls.posts,
            NUMBER_OF_POSTS_FROM_AUTHOR_WITH_FIRST_GROUP, )
        )
        Post.objects.bulk_create(cls.batch,
                                 NUMBER_OF_POSTS_FROM_AUTHOR_WITH_FIRST_GROUP,
                                 )
        cls.post = Post.objects.get(pk=1)
        cls.post_with_img = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.first_group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post_with_img,
            text='Тестовый комментарий',
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='NoName')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.post.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'Author'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_correct_context(self):
        """Провека корректности контекста страницы index."""
        response = self.client.get(reverse('posts:index'))
        self.assertTrue(response.context['page_obj'])
        self.assertTrue(response.context['title'])
        post = response.context['page_obj'][0]
        author = self.author
        text = 'Тестовый текст'
        group = self.first_group
        title = 'Последние обновления на сайте'
        self.assertEqual('posts/small.gif', post.image.name)
        self.assertEqual(author, post.author)
        self.assertEqual(text, post.text)
        self.assertEqual(group, post.group)
        self.assertEqual(title, response.context['title'])
        self.assertEqual(
            len(response.context['page_obj']),
            POSTS_ON_INDEX_PAGE,
        )

    def test_group_list_correct_context(self):
        """Провека корректности контекста страницы group_list."""
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'})
        )
        self.assertTrue(response.context['page_obj'])
        self.assertTrue(response.context['title'])
        post = response.context['page_obj'][0]
        author = self.author
        text = 'Тестовый текст'
        group = self.first_group
        title = 'Записи сообщества Тестовый заголовок 1'
        self.assertEqual(author, post.author)
        self.assertEqual('posts/small.gif', post.image.name)
        self.assertEqual(text, post.text)
        self.assertEqual(group, post.group)
        self.assertEqual(title, response.context['title'])
        self.assertEqual(
            len(response.context['page_obj']),
            POSTS_ON_GROUP_POSTS_PAGE,
        )

    def test_profile_correct_context(self):
        """Проверка корректности контекста страницы profile."""
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': 'Author'})
        )
        self.assertTrue(response.context['page_obj'])
        post = response.context['page_obj'][0]
        author = self.author
        text = 'Тестовый текст'
        group = self.first_group
        self.assertEqual(author, post.author)
        self.assertEqual('posts/small.gif', post.image.name)
        self.assertEqual(text, post.text)
        self.assertEqual(group, post.group)
        self.assertEqual(
            len(response.context['page_obj']),
            POSTS_ON_PROFILE_PAGE,
        )

    def test_post_detail_correct_context(self):
        """Проверяем корректность контекста страницы post_detail."""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 14})
        )
        self.assertTrue(response.context['post'])
        self.assertTrue(response.context['number_of_posts'])
        post = response.context['post']
        author = self.author
        group = self.first_group
        text = 'Тестовый текст'
        number_of_posts = response.context['number_of_posts']
        self.assertEqual('posts/small.gif', post.image.name)
        self.assertEqual(author, post.author)
        self.assertEqual(text, post.text)
        self.assertEqual(group, post.group)
        self.assertEqual(NUMBER_OF_ALL_CREATED_POSTS, number_of_posts)

    def test_create_post_correct_context(self):
        """Проверяем корректность контекста страницы create_post."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Проверяем корректность контекста страницы """
        response = self.post_author.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], True)

    def test_index_second_page_correct_records_number(self):
        # Проверка: на второй странице должно быть 4 поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            NUMBER_OF_ALL_CREATED_POSTS - POSTS_ON_INDEX_PAGE
        )

    def test_group_list_second_page_correct_records_number(self):
        # Проверка: на второй странице должно быть 4 поста.
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_profile_second_page_correct_records_number(self):
        # Проверка: на второй странице должно быть 4 поста.
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': 'Author'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_new_post_on_another_group_page(self):
        """Проверяем,что на странице группы first_group
        не появляются посты second_group
        """
        self.post_with_second_group = Post.objects.create(
            text='Тестовый текст второй группы',
            author=self.author,
            group=self.second_group
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'})
        )
        first_post_on_page = response.context['page_obj'][0].text
        self.assertNotEqual(first_post_on_page, 'Тестовый текст второй группы')

    def test_unauthorized_user_cant_comment(self):
        """Проверяем, что неавторизованный пользователь
        не может оставить комментарий.
        """
        response = self.guest_client.get(reverse(
            'posts:add_comment',
            kwargs={'post_id': 1})
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/posts/1/comment/'
        )

    def test_added_comment_is_on_post_detail_page(self):
        """Проверяем,что комментарии отображаются на странице поста."""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 14})
        )
        test_comment_text = 'Тестовый комментарий'
        response_comment_text = response.context['comments'][0].text
        self.assertEqual(test_comment_text, response_comment_text)

    def test_cache_index_page(self):
        """Тестирование корректной работы кэширования."""
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=14)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)

    def test_correct_follow_and_unfollow(self):
        """Проверяем, что подписка и отписка работают корректно."""
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(0, follow_count)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'Author'})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(1, follow_count)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'Author'})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(0, follow_count)

    def test_correct_follow_index_page_work(self):
        """Тестируем, что страница подписок работает корректно."""
        Post.objects.create(
            text='Тестируем follow_index_page',
            author=self.author,
            group=self.first_group,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts_on_page = len(response.context['page_obj'])
        self.assertEqual(0, posts_on_page)
        # подписываем пользователя NoName на пользователя Author
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'Author'})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        last_post = response.context['page_obj'][0].text
        self.assertEqual('Тестируем follow_index_page', last_post)

    def test_unauthorized_client_cannot_follow(self):
        """Тестируем, что неавторизованный пользователь
         не может подписаться
         """
        response = self.guest_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'Author'})
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fprofile%2FAuthor%2Ffollow%2F'
        )
