import base64
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile

from .serializers import UserSerializer

class ChatConsumer(WebsocketConsumer):

  def connect(self):
    print("connecting web socket india django")
    user = self.scope['user']
    if not user.is_authenticated:
      return
    
    # save username to use as a group name for this user
    self.username = user.username

    # join this user to a group with their username
    async_to_sync(self.channel_layer.group_add)(
      self.username,self.channel_name
    )
    
    self.accept()

  def disconnect(self, close_code):
    # /leave room/group
    # join this user to a group with their username
    async_to_sync(self.channel_layer.group_discard)(
      self.username,self.channel_name
    )
    
  # ----------------------------------
  # Handle requests
  # ----------------------------------

  def receive(self,text_data):
    # Receive message from web socket
    data = json.loads(text_data)
    data_source = data.get("source")
    # Pretty prit python dict
    print('recieve', json.dumps(data,indent=2))

    # Thumbnail upload
    if data_source == 'thumbnail':
      self.receive_thumbnail(data)

  def receive_thumbnail(self,data):
    user = self.scope['user']

    # convert base64 into django content file
    image_str = data.get('base64')
    image = ContentFile(base64.b64decode(image_str))
    print(image)
    # update thumbnail field
    filename = data.get('filename')
    user.thumbnail.save(filename,image,save=True)
    # serialize user
    serialized = UserSerializer(user)
    print('serialized==>',serialized)
    # send uploaded user data including new thumbnail
    self.send_group(self.username,'thumbnail',serialized.data)

  # catch/all broadcast to client helpers
  # 
  def send_group(self,group,source,data):
    response = {
      'type':'broadcast_group',
      'source':source,
      'data':data
    } 
    async_to_sync(self.channel_layer.group_send)(
      group,response
    )

  def broadcast_group(self,data):
    '''
      data:
        - type: 'broadcast_group'
        - source : where it originated from
        - data : what event you want to send as a dict
    '''
    data.pop('type')
    '''
      retun data:
        - source : where it originated from
        - data : what event you want to send as a dict
    '''
    self.send(text_data=json.dumps(data))

