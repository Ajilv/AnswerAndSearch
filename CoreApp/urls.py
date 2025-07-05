from django.urls import path,include
from CoreApp.views import UploadKnowledgeBase,AskQuestionView

urlpatterns=[
    path('upload-doc/', UploadKnowledgeBase.as_view(), name='upload-doc'),
    path('ask-question/', AskQuestionView.as_view(), name='ask-question'),
]