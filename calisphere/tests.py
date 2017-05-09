from django.test import Client

# Create your tests here.

c = Client()

c.get('/')
c.get('/exhibitions/')
