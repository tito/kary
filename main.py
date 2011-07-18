#!/usr/bin/env python
import kivy
kivy.require('1.0.7')

from os.path import dirname, isdir, join, exists
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics.fbo import Fbo
from kivy.graphics import RenderContext
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, \
        BooleanProperty
from kivy.resources import resource_add_path
from kivy.uix.floatlayout import FloatLayout

Builder.load_string('''
<SlideShaderContainer>:
	canvas:
		Rectangle:
			pos: self.pos
			size: self.size
			texture: self.fbo_texture

<Slides>:
	container1: container1
	container2: container2

    SlidesBackground:
        slides: root

	SlideShaderContainer:
		id: container1
		size_hint_y: None
		height: root.height - 35
		y: 35

	SlideShaderContainer:
		id: container2
		size_hint_y: None
		height: root.height - 35
		y: 35

    SlidesForeground:
        slides: root


<Slide>:
	pos_hint: {'x': 0, 'y': 0}

''')

fs_default = None
vs_default = '''
$HEADER$
uniform float alpha;
uniform vec2  size;
void main (void) {
  frag_color = color;
  tex_coord0 = vTexCoords0;
  vec2 p = vPosition.xy;
  p.x += alpha * size.x;
  //p.y += alpha * - size.y;
  gl_Position = projection_mat * modelview_mat * vec4(p, 0.0, 1.0);
}
'''

class SlideShaderContainer(FloatLayout):
    # (internal) This class is used to animate Slide instance.

    alpha = NumericProperty(0.)
    fbo = ObjectProperty(None)
    fbo_texture = ObjectProperty(None, allownone=True)
    vs = StringProperty(vs_default)
    fs = StringProperty(fs_default)

    def __init__(self, **kwargs):
        self.fbo = Fbo(size=self.size)
        self.fbo_texture = self.fbo
        self.canvas = RenderContext()
        self.canvas.shader.vs = self.vs
        self.canvas.shader.fs = self.fs
        self.canvas.add(self.fbo)
        Clock.schedule_interval(self.update_shader, 0)
        super(SlideShaderContainer, self).__init__(**kwargs)

    def _add_widget(self, widget):
        canvas = self.canvas
        self.canvas = self.fbo
        super(SlideShaderContainer, self).add_widget(widget)
        self.canvas = canvas

    def _remove_widget(self, widget):
        canvas = self.canvas
        self.canvas = self.fbo
        super(SlideShaderContainer, self).remove_widget(widget)
        self.canvas = canvas

    def on_size(self, instance, value):
        if value[0] < 1 or value[1] < 1:
            return
        self.fbo.size = value
        self.fbo_texture = self.fbo.texture

    def on_vs(self, instance, value):
        self.canvas.shader.vs = value

    def on_fs(self, instance, value):
        self.canvas.shader.fs = value

    def update_shader(self, dt):
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']
        self.canvas['alpha'] = float(self.alpha)
        self.canvas['size'] = map(float, self.size)


class SlidesBackground(FloatLayout):
    '''Widget used as a background of :class:`Slides` instance.
    '''

    #: Property that will contain the Slides instance
    slides = ObjectProperty(None)


class SlidesForeground(FloatLayout):
    '''Widget used as a foreground of :class:`Slides` instance.
    '''

    #: Property that will contain the Slides instance
    slides = ObjectProperty(None)


class Slide(FloatLayout):
    '''Base for creating Slide template.
    '''

    #: Property that indicate if this slide should be considered as a new
    #: section or not.
    is_section = BooleanProperty(False)

    #: Property that indicate the title of the Slide
    title = StringProperty(None)

    #: Indicate if this slide is currently showed on the screen or not
    active = BooleanProperty(False)


class Slides(FloatLayout):
    '''Root widget that must be used for creating a presentation.
    '''

    #: Current Slide to show
    container1 = ObjectProperty(None)

    #: Previous Slide showed
    container2 = ObjectProperty(None)

    #: Index of the previous slide
    old_index = NumericProperty(-1)

    #: Index of the current slide
    index = NumericProperty(0)

    #: Value of the current scrolling (between 0 to 1)
    scroll_x = NumericProperty(0)

    #: Contain the Clock.boottime(). Can be used for doing animation
    time = NumericProperty(0)

    #: Maximum available index
    max_index = NumericProperty(0)

    def __init__(self, **kwargs):
        self.slides = []
        super(Slides, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)
        Clock.schedule_interval(self.increase_time, 1 / 30.)
        Clock.schedule_once(self.init, 0)

    def init(self, dt):
        index = self.index
        self.index = -1
        self.index = index

    def increase_time(self, dt):
        self.time += dt

    def on_keyboard(self, instance, scancode, *largs):
        # down
        if scancode == 273:
            self.old_index = self.index
            for index in xrange(self.index+1, self.max_index):
                slide = self.slides[index]
                if slide.is_section:
                    self.index = index
                    return True
            return True
        # up
        if scancode == 274:
            self.old_index = self.index
            for index in xrange(self.index-1, -1, -1):
                slide = self.slides[index]
                if slide.is_section:
                    self.index = index
                    return True
            return True
        # home
        if scancode == 278:
            self.old_index = self.index
            self.index = 0
            return True
        # end
        if scancode == 279:
            self.old_index = self.index
            self.index = self.max_index - 1
            return True
        # left key
        if scancode == 275:
            self.old_index = self.index
            self.index = min(self.max_index - 1, self.index + 1)
            return True
        # right key
        if scancode == 276:
            self.old_index = self.index
            self.index = max(0, self.index - 1)
            return True

    def add_widget(self, widget):
        if isinstance(widget, Slide):
            self.slides.append(widget)
            self.max_index = len(self.slides)
            return
        return super(Slides, self).add_widget(widget)

    def on_index(self, instance, value):
        index = self.index
        old_index = self.old_index
        if index == old_index:
            return
        self.container2.clear_widgets()
        self.container2.add_widget(self.slides[index])
        d = 1. if index > old_index else -1.
        self.container2.alpha = d
        Animation(alpha=0., d=.3, t='out_quad').start(self.container2)
        self.slides[index].active = True
        if old_index != -1:
            self.container1.clear_widgets()
            self.container1.add_widget(self.slides[old_index])
            self.container1.alpha = 0.
            Animation(alpha=-d, d=.3, t='out_quad').start(self.container1)
            self.slides[old_index].active = False


class SlidesViewer(App):
    # Application for loading automatically the presentation
    # and contruct the user interface.

    def build(self):
        filename = self.options['filename']
        if isdir(filename):
            directory = filename
            filename = join(filename, 'presentation.kv')
        else:
            directory = dirname(filename)
        sys.path += [directory]
        resource_add_path(directory)
        template_fn = join(directory, 'templates.kv')
        if exists(template_fn):
            Builder.load_file(template_fn)
        return Builder.load_file(filename)


# Register some class to be used inside Kivy
Factory.register('Slides', cls=Slides)
Factory.register('SlidesBackground', cls=SlidesBackground)
Factory.register('SlidesForeground', cls=SlidesForeground)
Factory.register('Slide', cls=Slide)

# internal only
Factory.register('SlideShaderContainer', cls=SlideShaderContainer)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print 'Usage: main.py <filename.kv>'
        sys.exit(1)
    SlidesViewer(filename=sys.argv[1]).run()
