---
title: >
 {{post.title}}
date: {{post.date}}
abstract: >
 {{post.abstract}}
slug: {{post.slug}}
tags: {% if post.tags %}{{ post.tags|join(', ') }}{% endif %}
attached: {% if post.attachments %}{{ post.attachments|join(', ') }}{% endif %}
{% if post.location %}location:
 locality: {{post.location.locality}}
 country: {{post.location.country}}
 place: {{post.location.place}}
 long: {{post.location.longitude}}
 lat: {{post.location.latitude}}
{% endif %}
{% if post.weather %}weather:
 C: {{post.weather.temperature}}
 description: {{post.weather.description}}
 icon2: {{post.weather.icon}}
{% endif %}
image: {{post.image}}
---
{{ post.content|safe() }}

{# 
=======================================================
This template is used by "bucket3 new" to generate the 
markdown file of a new blog post.
=======================================================
#}