from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import staff_required

from .forms import AnnouncementForm
from .models import Announcement


def _can_manage(user, announcement):
    return user.is_admin or announcement.author_id == user.pk


def _visible_announcements(user):
    qs = Announcement.objects.select_related('author')
    if user.is_admin:
        return qs
    return qs.filter(
        Q(target_role__in=(Announcement.TARGET_ALL, user.role)) | Q(author=user)
    )


@login_required
def announcement_list(request):
    announcements = _visible_announcements(request.user)
    context = {
        'announcements': announcements,
        'can_post': request.user.is_admin or request.user.is_teacher,
    }
    return render(request, 'announcements/announcement_list.html', context)


@staff_required
def announcement_create(request):
    form = AnnouncementForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        announcement = form.save(commit=False)
        announcement.author = request.user
        announcement.save()
        messages.success(request, f'"{announcement.title}" has been posted.')
        return redirect('announcement_list')

    return render(request, 'announcements/announcement_form.html', {'form': form, 'announcement': None})


@staff_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if not _can_manage(request.user, announcement):
        messages.error(request, 'You do not have access to that page.')
        return redirect('announcement_list')

    form = AnnouncementForm(request.POST or None, instance=announcement, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{announcement.title}" has been updated.')
        return redirect('announcement_list')

    return render(request, 'announcements/announcement_form.html', {'form': form, 'announcement': announcement})


@staff_required
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if not _can_manage(request.user, announcement):
        messages.error(request, 'You do not have access to that page.')
        return redirect('announcement_list')

    if request.method == 'POST':
        title = announcement.title
        announcement.delete()
        messages.success(request, f'"{title}" has been removed.')
        return redirect('announcement_list')

    return render(request, 'announcements/announcement_confirm_delete.html', {'announcement': announcement})