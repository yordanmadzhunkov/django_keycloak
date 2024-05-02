from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class HelloView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    def get(self, request):
        print(request.headers)
        content = {'message': 'Hello, World!'}
        return Response(content)
    
    def post(self, request):
        #print(request.data)
        #print(request.data.keys())
        if request.data:
            content = {'message': 'Hello, ' + str(request.user) + " Your data is = " + str(request.data)}
        else:
            content = {'message': 'Invalid data!!!'}
        return Response(content)