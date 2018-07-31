from __future__ import unicode_literals
from __future__ import absolute_import

from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms
from django.db import models

# Register your models here.

from .models import *

class ExhibitItemInline(admin.TabularInline):
    model = ExhibitItem
    fields = ['order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as']
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['imgUrl', 'img_display']
    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class LessonPlanItemInline(admin.TabularInline):
    model = ExhibitItem
    fields = ['lesson_plan_order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as']
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['imgUrl', 'img_display']
    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class HistoricalEssayItemInline(admin.TabularInline):
    model = ExhibitItem
    fields = ['historical_essay_order', 'publish', 'item_id', 'essay', 'render_as', 'img_display', 'imgUrl', 'custom_crop', 'custom_link', 'custom_title', 'custom_metadata', 'metadata_render_as']
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'cols': 50, 'rows': 5})}
    }
    readonly_fields = ['imgUrl', 'img_display']
    def img_display(self, instance):
        if instance.imgUrl():
            return mark_safe("<img src='" + instance.imgUrl() + "'/>")
        else:
            return None
    img_display.short_description = "Thumbnail"

class NotesItemInline(admin.TabularInline):
    model = NotesItem
    fields = ['order', 'title', 'render_as', 'essay']
    verbose_name = 'Note'
    extra = 0

class HistoricalEssayExhibitInline(admin.TabularInline):
    model = HistoricalEssayExhibit
    fields = ['order', 'historicalEssay']
    extra = 0

class LessonPlanExhibitInline(admin.TabularInline):
    model = LessonPlanExhibit
    fields = ['order', 'lessonPlan']
    extra = 0

class ThemeExhibitInline(admin.TabularInline):
    model = ExhibitTheme
    fields = ['theme']
    verbose_name = 'Theme'
    extra = 0

class ExhibitThemeInline(admin.TabularInline):
    model = ExhibitTheme
    fields = ['order', 'exhibit']
    extra = 0

class HistoricalEssayThemeInline(admin.TabularInline):
    model = HistoricalEssayTheme
    fields = ['order', 'historicalEssay']
    extra = 0

class LessonPlanThemeInline(admin.TabularInline):
    model = LessonPlanTheme
    fields = ['order', 'lessonPlan']
    extra = 0

class BrowseTermInline(admin.TabularInline):
    model = BrowseTerm
    fields = ['order', 'link_text', 'link_location']
    extra = 0

class BrowseTermGroupInline(admin.TabularInline):
    model = BrowseTermGroup
    fields = ['order', 'group_title', 'group_note']
    extra = 0



class HistoricalEssayAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('blockquote')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')]}),
        ('Publish',                 {'fields': [('color', 'publish')]}),
        ('Essay',                   {'fields': [('essay', 'render_as'), ('go_further', 'go_further_render_as')], 'description': 'Use <code>&lt;h2&gt;</code> as the highest level heading for essays. Use <code>&lt;h4&gt;</code> for headings in Go Further.'}),
        ('About this Essay',        {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    inlines = [HistoricalEssayItemInline]
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                u"""<p>The text of this essay is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class ExhibitAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('short_title', 'blockquote')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')]}),
        ('Publish',                 {'fields': [('color', 'publish'), ('scraped_from')]}),
        ('Exhibit Overview',        {'fields': [('overview', 'render_as')]}),
        ('About this Exhibit',      {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    inlines = [ExhibitItemInline, NotesItemInline, ThemeExhibitInline, HistoricalEssayExhibitInline, LessonPlanExhibitInline, BrowseTermGroupInline]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                u"""<p>The text of this exhibition is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class LessonPlanAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('sub_title')]}),
        ('Lockup Image and Publish',{'fields': [('lockup_derivative', 'item_id'), ('publish')]}),
        ('Lesson Plan Overview',    {'fields': [('overview', 'render_as'), ('lesson_plan', 'grade_level')]}),
        ('About this Lesson Plan',  {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    prepopulated_fields = {'slug': ['title']}
    list_display = ('title', 'slug', 'get_absolute_url', 'publish')
    inlines = [LessonPlanItemInline]
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                u"""<p>The text of this lesson plan is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class BrowseTermGroupAdmin(admin.ModelAdmin):
    inlines = [BrowseTermInline]

class ThemeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                      {'fields': [('title', 'slug'), ('sort_title')]}),
        ('Hero Image and Lockup',   {'fields': [('hero', 'lockup_derivative'), ('item_id', 'alternate_lockup_derivative'), ('hero_first')]}),
        ('Publish',                 {'fields': [('color', 'publish'), ('category')]}),
        ('Theme Overview',          {'fields': [('essay', 'render_as')]}),
        ('About this Theme',        {'fields': [('byline', 'byline_render_as'), ('curator', 'copyright_holder'), ('copyright_year', 'credits_display')], 'classes': ['collapse']}),
        ('Metadata',                {'fields': [('meta_description', 'meta_keywords')], 'classes': ['collapse']})
    ]
    inlines = [ExhibitThemeInline, HistoricalEssayThemeInline, LessonPlanThemeInline, BrowseTermGroupInline]
    list_display = ('title', 'hero', 'hero_first', 'slug', 'get_absolute_url', 'publish')
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['credits_display']
    def credits_display(self, instance):
        if instance.curator or instance.copyright_year or instance.copyright_holder:
            return mark_safe(
                u"""<p>The text of this theme is available under a 
                <a href='https://creativecommons.org/licenses/by/4.0/'>Creative Commons 
                CC-BY license</a>. You are free to share and adapt it however you like, provided you 
                provide attribution as follows:</p><p>{0} curated by {1}, availabled under 
                a <a href="<a href='https://creativecommons.org/licenses/by/4.0/'>">CC BY 4.0 license</a>. 
                \u00A9 {2}, {3}.</p><p>Please note that this license applies 
                only to the descriptive copy and does not apply to any and all digital 
                items that may appear.</p>""".encode('utf-8').format(instance.title, instance.curator, 
                    instance.copyright_year, instance.copyright_holder)
                )
        else:
            return None
    credits_display.short_description = "Credits preview"

class ExhibitItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'exhibit', 'order', 'lesson_plan', 'lesson_plan_order', 'historical_essay', 'historical_essay_order')


admin.site.register(ExhibitItem, ExhibitItemAdmin)
admin.site.register(Exhibit, ExhibitAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(HistoricalEssay, HistoricalEssayAdmin)
admin.site.register(LessonPlan, LessonPlanAdmin)
admin.site.register(BrowseTermGroup, BrowseTermGroupAdmin)
