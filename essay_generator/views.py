from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import FormView

from .forms import FileFieldForm
from .models import Document

from django.conf import settings
import os

BASE_DIR = settings.BASE_DIR
SUM_TYPES = ('gensim', 'spacy', 'own')
SUM_FUNCS = {
    'gensim': Document.gensim_summary,
    'spacy': Document.spacy_summary,
    'own': Document.own_summary,
}


def perform_file_upload(file, filename: str) -> str:
    path = str(BASE_DIR) + f'/storage/{filename}'
    with open(path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    return path


def add_file_to_db(filepath: str) -> None:
    with open(filepath, 'rt', encoding='utf-8') as file:
        Document.objects.create(title=filepath.split('/')[-1].split('.')[0], text=file.read())
    os.remove(filepath)


# Create your views here.
def index(request):
    return render(request, 'index.html', context={'documents': Document.objects.all()})


def document(request, pk=None, sum_type='gensim'):
    if pk is not None:
        obj = get_object_or_404(Document, pk=pk)
        if sum_type in SUM_TYPES:
            func = SUM_FUNCS[sum_type]
            return render(request, 'document.html',
                          context={'document': obj, 'essay': func(obj), 'keywords': obj.keywords()})
    return redirect(reverse('index'))


class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = 'upload.html'  # Replace with your template.
    success_url = '/'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                add_file_to_db(perform_file_upload(f, f.name))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def chose_files():
    pass


def show_results():
    pass
