from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth import get_user_model
from films.models import Film, UserFilms
from django.views.generic.list import ListView
from django.contrib import messages
from films.forms import RegisterForm
from films.utils import get_max_order, reorder
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
    model = UserFilms
    template_name = "films.html"
    paginate_by = 15 # used to handle pagination. gives template tag page_obj to handle sending page number to view by querry parameters ex. src={{page_obj.number|add:1}}
    context_object_name = 'films' # variable name used in template

    def get_template_names(self):
        if self.request.htmx:
             return 'partials/film-list-elements.html'
        else:
            return 'films.html'

    def get_queryset(self):
        # return UserFilms.objects.filter(user=self.request.user) # use many to many model to extract user films
        # prefetch related object from db to reduce number of querries (used for many to many)
        return UserFilms.objects.prefetch_related('film').filter(user=self.request.user) # use many to many model to extract user films




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

    # request.user.films.add(film)

    #add the film to the user's list with order
    if not UserFilms.objects.filter(film=film, user=request.user).exists():
        UserFilms.objects.create(film=film, user=request.user, order=get_max_order(request.user))

    #return tempate with all of the user's films
    films = UserFilms.objects.filter(user=request.user)
    messages.success(request, f"Added {name} to list of films")
    return render(request, 'partials/film-list.html', {"films": films})


@login_required
@require_http_methods(['DELETE'])
def delete_film(request, pk): ## pk must match parameter in url path
    # remove the film from user's list
    # request.user.films.remove(pk)
    UserFilms.objects.get(pk=pk).delete()
    # return tempate with all of the user's films
    films = UserFilms.objects.filter(user=request.user)
    reorder(request.user)
    return render(request, 'partials/film-list.html', {"films": films})


def search_film(request):
    search_text = request.POST.get("search")

    userfilms = UserFilms.objects.filter(user=request.user)
    # taxi driver match Taxi Driver
    results = Film.objects.filter(name__icontains=search_text).exclude(
        name__in=userfilms.values_list('film__name', flat=True) # wylaczenie z listy nazw filmow ktore juz sa w bazie dla tego usera
    )
    context = {'results': results}
    return render(request, 'partials/search-results.html', context)


def clear(request):
    return HttpResponse("")

def sort(request):
    films_pks_order = request.POST.getlist('film_order')
    print(films_pks_order)
    films = []
    updated_films = []

    userfilms = UserFilms.objects.prefetch_related('film').filter(user=request.user)

    for index , film_pk in enumerate(films_pks_order, start=1):
        # userfilm = UserFilms.objects.get(pk=film_pk)
        # avoid querry to db every iteration
        userfilm = next(u for u in userfilms if u.pk == int(film_pk))

        if userfilm.order != index:
            userfilm.order = index
            updated_films.append(userfilm)

        films.append(userfilm)

    # bulk update instead of update every iteration
    UserFilms.objects.bulk_update(updated_films, ['order'])

    return render(request, 'partials/film-list.html', {"films": films})

@login_required
def detail(request, pk):
    userfilm = get_object_or_404(UserFilms, pk=pk)
    context = {'userfilm': userfilm}
    return render(request, 'partials/film-detail.html', context=context)

@login_required
def film_partial(request):
    context = {"films": UserFilms.objects.filter(user=request.user)}
    return render(request, 'partials/film-list.html', context)


@login_required
def upload_photo(request, pk):
    userfilm = get_object_or_404(UserFilms, pk=pk)
    print(request.FILES)  # uploaded photo
    photo = request.FILES.get("photo")
    userfilm.film.photo.save(photo.name, photo)
    context = {'userfilm': userfilm}
    return render(request, 'partials/film-detail.html', context=context)
