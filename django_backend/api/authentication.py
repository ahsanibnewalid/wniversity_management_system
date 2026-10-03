from rest_framework.authentication import BaseAuthentication
from django_backend.legacy.models import AuthToken, User
class BearerTokenAuthentication(BaseAuthentication):
    keyword="Bearer"
    def authenticate(self,request):
        header=request.headers.get("Authorization","")
        if not header.startswith(self.keyword+" "): return None
        token=header[len(self.keyword)+1:].strip()
        row=AuthToken.objects.filter(token=token,revoked=False).first()
        if not row: return None
        user=User.objects.filter(pk=row.user_id).first()
        return (user,token) if user else None
