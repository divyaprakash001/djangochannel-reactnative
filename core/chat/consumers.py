import base64
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile

from .models import User, Connection
from django.db.models import Q,  Exists, OuterRef
from .serializers import SearchSerializer, UserSerializer, RequestSerializer, FriendSerializer

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
    print('recieve-==>', json.dumps(data,indent=2))

    # Thumbnail upload
    if data_source == 'thumbnail':
      self.receive_thumbnail(data)

    # search / filter for users
    elif(data_source == 'search'):
      self.receive_search(data)

    # make friend request request.connect
    elif(data_source == 'request.connect'):
      self.receive_request_connect(data)

    # get request lists  request.list
    elif(data_source == 'request.list'):
      print("request list call hua")
      self.receive_request_list(data)


    # accept request request.accept
    elif(data_source == 'request.accept'):
      print("request accept call hua")
      self.receive_request_accept(data)

    # accept request request.accept
    elif(data_source == 'friend.list'):
      print("request accept call hua")
      self.receive_request_friends(data)

  def receive_thumbnail(self,data):
    user = self.scope['user']

    # convert base64 into django content file
    image_str = data.get('base64')
    image = ContentFile(base64.b64decode(image_str))
    # update thumbnail field
    filename = data.get('filename')
    user.thumbnail.save(filename,image,save=True)
    # serialize user
    serialized = UserSerializer(user)
    # send uploaded user data including new thumbnail
    self.send_group(self.username,'thumbnail',serialized.data)


  def receive_request_connect(self,data):
    username = data.get("username")
    # attempt to fetch the receiving user
    try:
      receiver = User.objects.get(username=username)
      print("receiver==>",receiver)
    except User.DoesNotExist:
      print("error : user not found")
      return
    
    # create connection
    connection, _ = Connection.objects.get_or_create(
      sender = self.scope['user'],
      receiver = receiver
    )

    # serialized connection
    serialized = RequestSerializer(connection)

    # send back to sender
    self.send_group(connection.sender.username,'request.connect',serialized.data)

    # send to receiver
    self.send_group(
      connection.receiver.username, 'request.connect', serialized.data
    )


# receive request list
  def receive_request_list(self,data):
    user = self.scope['user']
    # get the connection made to this user
    connections = Connection.objects.filter(
      receiver=user,
      accepted=False
    )

    # serialized connection
    serialized = RequestSerializer(connections,many=True)

    # send request lists to this user
    print(connections)
    self.send_group(user.username,'request.list',serialized.data)
    




# receive request accept receive_request_accept
  def receive_request_accept(self,data):
    print("receive accept call hua")
    user = self.scope['user']
    username = data.get('username')

    # sender = User.objects.get(username=username)
    # get the connection made to this user
    try:
      connection = Connection.objects.get(
      sender__username=username,
      receiver=user,
      accepted=False
      )
    except Connection.DoesNotExist:
      print("Error:: connection does not exists")
      return

    # update the connection to accepted=true
    connection.accepted = True
    connection.save()
    print("connection-->", connection.accepted)

    # serialized connection
    serialized = RequestSerializer(connection)

    # send accepted request to sender
    self.send_group(connection.sender.username,'request.accept',serialized.data)

    # send accepted request to receiver
    self.send_group(connection.receiver.username,'request.accept',serialized.data)
    

#  request friends
  def receive_request_friends(self,data):
    print("friend list call hua")
    user = self.scope['user']
    # username = data.get("username")
    # get the connection made to this user
    connections = Connection.objects.filter(
      Q(sender=user)|Q(receiver=user),
      accepted=True
    )

    print("maine sare connections print krke de diya",connections)
    # serialized connection
    serialized = FriendSerializer(connections, 
                                  context={'user':user} ,
                                  many=True)

    # send request lists to this user
    print(connections)
    self.send_group(user.username,'friend.list',serialized.data)
    


# user search
  def receive_search(self,data):
    # ...
    query = data.get('query')
    # get users from query seach form
    users = User.objects.filter(
      Q(username__istartswith=query) | 
      Q(first_name__istartswith=query) | 
      Q(last_name__istartswith=query)       
      ).exclude(
        username=self.username
      ).annotate(
        pending_them= Exists(
          Connection.objects.filter(
            sender=self.scope['user'],
            receiver = OuterRef('id'),
            accepted=False
          )
        ),
        
        pending_me= Exists(
          Connection.objects.filter(
            sender= OuterRef('id'),
            receiver = self.scope['user'],
            accepted=False
          )
        ),

        connected= Exists(
          Connection.objects.filter(
           Q(sender=self.scope['user'], receiver = OuterRef('id')) |
           Q(receiver=self.scope['user'], sender = OuterRef('id')) ,
           accepted=True
          )
        ),

      )
    # serialize the results
    serialized = SearchSerializer(users,many=True)
    # send search results back to this user
    self.send_group(self.username,'search',serialized.data)



  # catch/all broadcast to client helpers
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

