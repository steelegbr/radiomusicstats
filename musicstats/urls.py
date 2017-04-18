from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/logsongplay', views.log_song_play),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
