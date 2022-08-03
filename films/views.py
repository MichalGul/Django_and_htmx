from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth import get_user_model
from films.models import Film
from django.views.generic.list import ListView
from django.contrib import messages
from films.forms import RegisterForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

# Create your views here.
class IndexView(TemplateView):
    template_name = 'index.html'
    
class Login(LoginView):
    template_name = 'registration/login.html'

class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()  # save the user
        return super().form_valid(form)

class FilmList(LoginRequiredMixin, ListView):
    model = Film
    template_name = "films.html"
    context_object_name = 'films' # variable name used in template

    def get_queryset(self):
        user = self.request.user
        return user.films.all()




def check_username(request):
    username = request.POST.get("username")
    if get_user_model().objects.filter(username=username).exists():
        return HttpResponse("<div id='username-error' class='error'>'This username already exists</div>")
    else:
        return HttpResponse("<div id='username-error' class='success'>This username is avaliable</div>")


@login_required
def add_film(request):
    name = request.POST.get("filmname")
    film = Film.objects.get_or_create(name=name)[0] # creating element in database (no neet for save()

    #add the film to the user's list
    request.user.films.add(film)

    #return tempate with all of the user's films
    films = request.user.films.all()
    messages.success(request, f"Added {name} to list of films")
    return render(request, 'partials/film-list.html', {"films": films})


@login_required
@require_http_methods(['DELETE'])
def delete_film(request, pk): ## pk must match parameter in url path
    # remove the film from user's list
    request.user.films.remove(pk)

    # return tempate with all of the user's films
    films = request.user.films.all()
    return render(request, 'partials/film-list.html', {"films": films})


def search_film(request):
    search_text = request.POST.get("search")

    userfilms = request.user.films.all()
    # taxi driver match Taxi Driver
    results = Film.objects.filter(name__icontains=search_text).exclude(
        name__in=userfilms.values_list('name', flat=True) # wylaczenie z listy nazw filmow ktore juz sa w bazie dla tego usera
    )
    context = {'results': results}
    return render(request, 'partials/search-results.html', context)


def clear(request):
    return HttpResponse("")