from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from exhibits.models import *
from itertools import chain
import random

def calCultures(request):
    california_cultures = Theme.objects.filter(title__icontains='California Cultures', publish=True).order_by('title')

    unique_historical_essays = HistoricalEssay.objects.filter(historicalessaytheme__theme__in=california_cultures, publish=True).values_list('title', 'id').distinct()
    historical_essays = []
    for (title, key) in unique_historical_essays:
        historical_essays.append(HistoricalEssay.objects.get(pk=key))

    unique_lesson_plans = LessonPlan.objects.filter(lessonplantheme__theme__in=california_cultures, publish=True).values_list('title', 'id').distinct()
    lesson_plans = []
    for (title, key) in unique_lesson_plans:
        lesson_plans.append(LessonPlan.objects.get(pk=key))

    return render(request, 'exhibits/calCultures.html', {
        'california_cultures': california_cultures, 
        'historical_essays': historical_essays,
        'lesson_plans': lesson_plans
    })

def exhibitRandom(request):
    exhibits = Exhibit.objects.filter(publish=True)
    themes = Theme.objects.filter(publish=True)
    exhibit_theme_list = list(chain(exhibits, themes))
    random.shuffle(exhibit_theme_list)

    exhibit_theme_list_by_fives = []
    sublist = []
    count = 0

    for index, item in enumerate(exhibit_theme_list):
        if isinstance(item, Exhibit):
            if count < 5:
                sublist.append(('exhibit', item))
                count += 1
            else:
                exhibit_theme_list_by_fives.append(sublist)
                sublist = [('exhibit', item)]
                count = 1
        elif isinstance(item, Theme):
            if count < 4:
                sublist.append(('theme', item))
                count +=2
            elif count < 5:
                # find next instance of exhibit and swap this theme for that exhibit
                for swap in range(index+1, len(exhibit_theme_list)):
                    if isinstance(exhibit_theme_list[swap], Exhibit):
                        tmp = exhibit_theme_list[swap]
                        exhibit_theme_list[swap] = exhibit_theme_list[index]
                        exhibit_theme_list[index] = tmp
                        break

                if isinstance(exhibit_theme_list[index], Exhibit):
                    sublist.append(('exhibit', exhibit_theme_list[index]))
                    count += 1
                else:
                    # haven't found anything to swap with, so this will be a short row
                    exhibit_theme_list_by_fives.append(sublist)
                    sublist = [('theme', item)]
                    count = 2
            else:
                exhibit_theme_list_by_fives.append(sublist)
                sublist = [('theme', item)]
                count = 2

    exhibit_theme_list_by_fives.append(sublist)

    return render(request, 'exhibits/exhibitRandomExplore.html', {'sets': exhibit_theme_list_by_fives, 'sets_standard': exhibit_theme_list})

def exhibitSearch(request):
    if request.method == 'GET' and len(request.GET.getlist('title')) > 0:
        exhibits = Exhibit.objects.filter(title__icontains=request.GET['title'], publish=True).order_by('title')
        return render(request, 'exhibits/exhibitSearch.html', {'searchTerm': request.GET['title'], 'exhibits': exhibits})
    else: 
        exhibits = Exhibit.objects.all().filter(publish=True).order_by('title')
        return render(request, 'exhibits/exhibitSearch.html', {'searchTerm': '', 'exhibits': exhibits})

def exhibitDirectory(request, category='search'):
    if category in list(category for (category, display) in Theme.CATEGORY_CHOICES):
        themes = Theme.objects.filter(category=category, publish=True).order_by('sort_title')
        collated = []
        for theme in themes:
            exhibits = Exhibit.objects.filter(exhibittheme__theme=theme, publish=True)
            collated.append((theme, exhibits))
        return render(request, 'exhibits/exhibitDirectory.html', {'themes': collated, 'categories': Theme.CATEGORY_CHOICES, 'selected': category})
        
    if category == 'all': 
        exhibits = Exhibit.objects.all().filter(publish=True).order_by('title')
    if category == 'uncategorized':

        # if exhibit's theme is null OR if exhibit's theme is unpublished, but the exhibit is published
        exhibitsWithNoTheme = Exhibit.objects.filter(exhibittheme__isnull=True, publish=True)
        exhibitsWithUnpublishedTheme = Exhibit.objects.filter(exhibittheme__theme__publish=False, publish=True)
        exhibits = exhibitsWithNoTheme | exhibitsWithUnpublishedTheme

    return render(request, 'exhibits/exhibitDirectory.html', {'themes': [{'', exhibits}], 'categories': Theme.CATEGORY_CHOICES, 'selected': category})

def themeDirectory(request):
    jarda = Theme.objects.get(slug='jarda')
    california_cultures = Theme.objects.filter(title__icontains='California Cultures').order_by('title')
    california_history = Theme.objects.exclude(title__icontains='California Cultures').exclude(slug='jarda')
    return render(request, 'exhibits/themeDirectory.html', {'jarda': jarda, 'california_cultures': california_cultures, 'california_history': california_history})

def lessonPlanDirectory(request):
    lessonPlans = LessonPlan.objects.filter(publish=True)
    historicalEssays = HistoricalEssay.objects.filter(publish=True)
    return render(request, 'exhibits/for-teachers.html', {'lessonPlans': lessonPlans, 'historicalEssays': historicalEssays})

def itemView(request, exhibit_id, item_id):
    fromExhibitPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    exhibitItem = get_object_or_404(ExhibitItem, item_id=item_id, exhibit=exhibit_id)
    try:
        nextItem = ExhibitItem.objects.get(exhibit=exhibit_id, order=exhibitItem.order+1)
    except ObjectDoesNotExist:
        nextItem = None
    try:
        prevItem = ExhibitItem.objects.get(exhibit=exhibit_id, order=exhibitItem.order-1)
    except ObjectDoesNotExist:
        prevItem = None

    if fromExhibitPage:
        return render(request, 'exhibits/itemView.html', {'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})
    else:
        exhibit = get_object_or_404(Exhibit, pk=exhibit_id, publish=True)
        exhibitItems = exhibit.exhibititem_set.all().order_by('order')
        exhibitListing = []
        for theme in exhibit.exhibittheme_set.all():
            exhibitListing.append((theme.theme, theme.theme.exhibittheme_set.exclude(exhibit=exhibit).order_by('order')))
        return render(request, 'exhibits/itemView.html',
        {'exhibit': exhibit, 'q': '', 'exhibitItems': exhibitItems, 'relatedExhibitsByTheme': exhibitListing, 'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})

def lessonPlanItemView(request, lesson_id, item_id):
    fromLessonPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    exhibitItem = get_object_or_404(ExhibitItem, item_id=item_id, lesson_plan=lesson_id)
    try:
        nextItem = ExhibitItem.objects.get(lesson_plan=lesson_id, lesson_plan_order=exhibitItem.lesson_plan_order+1)
    except ObjectDoesNotExist:
        nextItem = None
    try:
        prevItem = ExhibitItem.objects.get(lesson_plan=lesson_id, lesson_plan_order=exhibitItem.lesson_plan_order-1)
    except ObjectDoesNotExist:
        prevItem = None

    if fromLessonPage:
        return render(request, 'exhibits/lessonItemView.html', {'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})
    else:
        lesson = get_object_or_404(LessonPlan, pk=lesson_id, publish=True)
        exhibitItems = lesson.exhibititem_set.all().order_by('lesson_plan_order')
        return render(request, 'exhibits/lessonItemView.html',
        {'lessonPlan': lesson, 'q': '', 'exhibitItems': exhibitItems, 'exhibitItem': exhibitItem, 'nextItem': nextItem, 'prevItem': prevItem})

def exhibitView(request, exhibit_id, exhibit_slug):
    fromExhibitPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    if fromExhibitPage:
        return render(request, 'exhibits/pjaxTemplates/pjax-exhibit-item.html')

    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    if exhibit_slug != exhibit.slug:
        return redirect(exhibit)
    if not exhibit.publish:
        raise Http404("Exhibit is unpublished");

    exhibitItems = exhibit.exhibititem_set.all().order_by('order')
    exhibitListing = []
    for theme in exhibit.exhibittheme_set.filter(theme__publish=True).all():
        exhibits = theme.theme.exhibittheme_set.exclude(exhibit=exhibit).filter(exhibit__publish=True).order_by('order')
        if exhibits.count() > 0:
            exhibitListing.append((theme.theme, exhibits))

    return render(request, 'exhibits/exhibitView.html',
    {'exhibit': exhibit, 'q': '', 'exhibitItems': exhibitItems, 'relatedExhibitsByTheme': exhibitListing})

def essayView(request, essay_id, essay_slug):
    essay = get_object_or_404(HistoricalEssay, pk=essay_id)
    if essay_slug != essay.slug:
        return redirect(essay)
    if not essay.publish:
        raise Http404("Essay is unpublished");

    return render(request, 'exhibits/essayView.html', {'essay': essay, 'q': ''})

def themeView(request, theme_id, theme_slug):
    theme = get_object_or_404(Theme, pk=theme_id)
    if theme_slug != theme.slug:
        return redirect(theme)
    if not theme.publish:
        raise Http404("Theme is unpublished");

    exhibitListing = theme.exhibittheme_set.filter(exhibit__publish=True).order_by('order')
    return render(request, 'exhibits/themeView.html', {'theme': theme, 'relatedExhibits': exhibitListing})

def lessonPlanView(request, lesson_id, lesson_slug):
    fromLessonPage = request.META.get("HTTP_X_EXHIBIT_ITEM")
    if fromLessonPage:
        return render(request, 'exhibits/pjaxTemplates/pjax-exhibit-item.html')

    lesson = get_object_or_404(LessonPlan, pk=lesson_id)
    if lesson_slug != lesson.slug:
        return redirect(lesson)
    if not lesson.publish:
        raise Http404("Lesson plan is unpublished");

    exhibitItems = lesson.exhibititem_set.all().order_by('lesson_plan_order')
    
    relatedThemes = []
    for theme in lesson.lessonplantheme_set.filter(theme__publish=True):
        relatedThemes.append((theme.theme, theme.theme.lessonplantheme_set.exclude(lessonPlan=lesson)))
    
    return render(request, 'exhibits/lessonPlanView.html', {'lessonPlan': lesson, 'q': '', 'exhibitItems': exhibitItems, 'relatedThemes': relatedThemes})
