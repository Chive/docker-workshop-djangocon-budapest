import os

from django.core.cache import cache
from django.views.generic import TemplateView

CACHE_KEY = 'counter'


class IndexView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        self.counter = cache.get(CACHE_KEY, 0) + 1
        cache.set(CACHE_KEY, self.counter)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'counter': self.counter,
            'hostname': os.environ.get('HOSTNAME'),
        })
        return context


index = IndexView.as_view()
