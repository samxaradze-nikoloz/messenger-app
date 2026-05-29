import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id   = self.scope['url_route']['kwargs']['chat_id']
        self.room_name = f'chat_{self.chat_id}'
        self.user      = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Check membership
        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Broadcast "user online"
        await self.channel_layer.group_send(self.room_name, {
            'type':     'user_status',
            'username': self.user.username,
            'online':   True,
        })

    async def disconnect(self, code):
        await self.channel_layer.group_send(self.room_name, {
            'type':     'user_status',
            'username': self.user.username,
            'online':   False,
        })
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'message':
            await self.channel_layer.group_send(self.room_name, {
                'type':       'chat_message',
                'id':         data.get('id'),
                'body':       data.get('body', ''),
                'image_url':  data.get('image_url'),
                'msg_type':   data.get('msg_type', 'text'),
                'sender':     self.user.username,
                'sender_av':  data.get('sender_av'),
                'created_at': data.get('created_at'),
                'reply_to':   data.get('reply_to'),
            })

        elif event_type == 'typing':
            await self.channel_layer.group_send(self.room_name, {
                'type':     'typing_indicator',
                'username': self.user.username,
                'typing':   data.get('typing', False),
            })

        elif event_type == 'read':
            await self.mark_read()
            await self.channel_layer.group_send(self.room_name, {
                'type':     'read_receipt',
                'username': self.user.username,
            })

        elif event_type == 'call_signal':
            # Forward WebRTC signaling
            await self.channel_layer.group_send(self.room_name, {
                'type':   'call_signal',
                'signal': data.get('signal'),
                'from':   self.user.username,
            })

    # ── Handlers ─────────────────────────────────────────────────

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type':       'message',
            'id':         event['id'],
            'body':       event['body'],
            'image_url':  event.get('image_url'),
            'msg_type':   event['msg_type'],
            'sender':     event['sender'],
            'sender_av':  event.get('sender_av'),
            'created_at': event['created_at'],
            'reply_to':   event.get('reply_to'),
            'is_mine':    event['sender'] == self.user.username,
        }))

    async def typing_indicator(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type':     'typing',
                'username': event['username'],
                'typing':   event['typing'],
            }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type':     'read',
            'username': event['username'],
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type':     'status',
            'username': event['username'],
            'online':   event['online'],
        }))

    async def call_signal(self, event):
        if event['from'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type':   'call_signal',
                'signal': event['signal'],
                'from':   event['from'],
            }))

    # ── DB helpers ────────────────────────────────────────────────

    @database_sync_to_async
    def check_membership(self):
        from .models import Chat
        return Chat.objects.filter(id=self.chat_id, members=self.user).exists()

    @database_sync_to_async
    def mark_read(self):
        from .models import ChatMember
        ChatMember.objects.filter(
            chat_id=self.chat_id, user=self.user
        ).update(last_read=timezone.now())