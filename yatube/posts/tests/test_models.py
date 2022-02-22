from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст длинной больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Тестирование метода __str__ у моделей Post и Group"""
        str_post = str(PostModelTest.post)
        str_group = str(PostModelTest.group)
        dict_of_titles = {
            str_post: 'Тестовый текст ',
            str_group: 'Тестовая группа',
        }
        for title, expected_title in dict_of_titles.items():
            with self.subTest(title=title):
                self.assertEqual(title, expected_title)
