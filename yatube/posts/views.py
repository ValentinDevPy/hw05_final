from typing import Dict

from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow

POSTS_ON_INDEX_PAGE = 10
POSTS_ON_GROUP_POSTS_PAGE = 10
POSTS_ON_PROFILE_PAGE = 10

User = get_user_model()


def index(request: HttpRequest) -> HttpResponse:
    """"Обработка запросов к главной странице."""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_ON_INDEX_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title: str = "Последние обновления на сайте"
    context: Dict = {
        'title': title,
        'page_obj': page_obj,
        'index': True,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug) -> HttpResponse:
    """Обработка запросов к странице конкретного сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, POSTS_ON_GROUP_POSTS_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title: str = f'Записи сообщества {group.title}'
    context: Dict = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Отображение всех постов конкретного пользователя."""
    if request.user.is_authenticated:
        follow = User.objects.get(username=username)
        following = (
            Follow.objects
            .filter(user=request.user, author=follow)
            .exists()
        )
    else:
        following = False
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, POSTS_ON_PROFILE_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Отображение подробной информации по одному посту."""
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    number_of_posts = Post.objects.filter(author=author).count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'number_of_posts': number_of_posts,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Создание нового поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        form.save()
        return redirect(f'/profile/{request.user}/')
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Редактирование существующего поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами отслеживаемых людей."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, POSTS_ON_INDEX_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title: str = "Последние обновления на сайте"
    context: Dict = {
        'title': title,
        'page_obj': page_obj,
        'follow': True,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow = get_object_or_404(User, username=username)
    if follow != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=follow,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(User, username=username)
    is_exist = (
        Follow.objects
        .filter(user=request.user, author=follow)
        .exists()
    )
    if is_exist:
        Follow.objects.filter(user=request.user, author=follow).delete()
    return redirect('posts:profile', username=username)
