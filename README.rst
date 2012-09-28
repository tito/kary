

Kary - Presentation based on Kivy language
==========================================

Kary is a tool to create presentation using Kivy language.

Installation
------------

You need to have Kivy 1.0.7 minimum to make it run (http://kivy.org/)


Usage
-----

::

  kary <directory_of_your_presentation>

  OR

  kary <filename.kv>


How does it work ?
------------------

Kary is defining few classes needed for creating slides:

- Slides: a widget that will contain a list of Slide. It must be your root
  widget, and cannot be used inside another widgets.
- Slide: base widget for constructing more complex Slide, like with or without
  title, with image content, or video content etc.
- SlidesBackground: this widget will be always created by Slides. Add a rule if
  you want to customize the background of slides.
- SlidesForeground: this widget will be always created by Slides. Add a rule if
  you want to customize the foreground of slides.

Create a directory with this layout::

  mypresentation/
    presentation.kv
    templates.kv (optional)
    ... (put any files you want to use in the kv)

In `templates.kv`, you could define some Kivy template to be used in your `presentation.kv`::

    #: kivy 1.0

    # For all your slides, you want to have the same Label for representing
    # a title, with always the same background and settings.
    [Title@Label]:
        text: ctx.text
        text_size: self.width - 60, None
        halign: 'left'
        size_hint_y: None
        height: 100
        font_size: 36
        color: labelcolor
        canvas.before:
            Color:
                rgba: 0, 0, 0, .2
            Rectangle:
                pos: self.pos
                size: self.size

    # This is a simple slide with title on top and content on bottom.
    [SlideContent@Slide]:
        GridLayout:
            pos: root.pos
            cols: 1
            Title:
                text: ctx.title
            BoxLayout:
                padding: 50
                Label:
                    color: labelcolor
                    text: ''.join(ctx.content)
                    font_size: ctx.get('font_size', 36)
                    text_size: self.width, None

Then, in the `presentation.kv`, you can use it like that::

    #!/usr/bin/env kary
    #:kivy 1.0

    Slides:

        SlideContent:
            title: 'Hello world'
            content:
                ('This is the first line\n',
                'This is the second line')

        SlideContent:
            title: 'My last slide'
            content: ('Any questions ?, )

Then, open a terminal, and type::

    kary mypresentation

And your presentation will be opened !


Keyboard shortcuts
------------------

- Left: previous slide
- Right: next slide
- Up: next section
- Down: previous section slide
- Home: first slide slide
- End: last slide

