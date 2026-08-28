from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MessageForm
from .models import Message


@login_required
def message_inbox(request):
    received = (
        Message.objects.filter(receiver=request.user)
        .select_related('sender')
        .order_by('read', '-created_at')
    )
    return render(request, 'messaging/inbox.html', {'message_list': received})


@login_required
def message_sent(request):
    sent = (
        Message.objects.filter(sender=request.user)
        .select_related('receiver')
    )
    return render(request, 'messaging/sent.html', {'message_list': sent})


@login_required
def message_compose(request):
    initial = {'receiver': request.GET.get('to')}
    form = MessageForm(request.POST or None, user=request.user, initial=initial)
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.save()
        messages.success(request, f'Your message to {message.receiver.display_name} has been sent.')
        return redirect('message_sent')

    return render(request, 'messaging/compose.html', {'form': form})


@login_required
def message_detail(request, pk):
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver'),
        pk=pk,
    )
    if request.user.pk not in (message.sender_id, message.receiver_id):
        messages.error(request, 'You do not have access to that page.')
        return redirect('message_inbox')

    if message.receiver_id == request.user.pk and not message.read:
        message.read = True
        message.save(update_fields=['read'])

    context = {'message': message}
    return render(request, 'messaging/message_detail.html', context)