import copy
from django import forms
from django import template
from django.template import Context
from django.template.loader import get_template
from django.utils.datastructures import SortedDict

register = template.Library()

class FieldsetNode(template.Node):
    def __init__(self, fields, variable_name, form_variable):
        self.fields = fields
        self.variable_name = variable_name
        self.form_variable = form_variable

    def render(self, context):
        form = template.Variable(self.form_variable).resolve(context)
        new_form = copy.copy(form)
        new_form.fields = SortedDict(
            [(key, form.fields[key]) for key in self.fields]
        )
        context[self.variable_name] = new_form
        return u''

@register.tag(name='get_fieldset')
def get_fieldset(parser, token):
    """
    A simple templatetag to split form fields into fieldsets from the template.

    Usage:
    {% load fieldsets %}

    {% get_fieldset slug,name,description,maintainers,tags as simple_fields from project_form %}
    {% for field in simple_fields %}
        {{ field }}
    </div>
    {% endfor %}
    """
    try:
        name, fields, as_, variable_name, from_, form = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('Bad arguments for %r' % token.split_contents()[0])

    return FieldsetNode(fields.split(','), variable_name, form)

@register.tag(name="dual_form")
def dual_form(parser, token):
    """
        Template tag used to help with forms that appear in twin columns.

        usage: {% dual_form FIELD[,FIELD] from FORM as POSITION %}

        Replaces the templatetag with a list of divs that contain the fields
        along  with the labels, error messages, etc.
        Fields with error messages are decorated with the 'tx-form-error' class

        example:
        <form action="" method="post">
            {% dual_form first_name,location,blog,about from form as left %}
            {% dual_form last_name,languages,linkedin,twitter,looking_for_work from form as right %}
            {% dual_form looking_for_work from form as fullrow %}
            <div class="submit-button">
                <input type="submit" value="{% trans "Save changes" %}" />
            </div>
        </form>
    """

    contents = token.split_contents()
    try:
        name, fields, from_, form, as_, position = contents
    except ValueError, e:
        raise template.TemplateSyntaxError(
            "Bad arguments for %s, "\
            "usage: %s FIELD[,FIELD] from FORM as POSITION" % contents[0]
        )

    return DualFormNode(fields.split(','), form, position)

class DualFormNode(template.Node):
    def __init__(self, fields, form_variable, position):
        if position not in ('left', 'right', 'fullrow', ):
            raise template.TemplateSyntaxError(
                "usage: %s FIELD[,FIELD] from FORM as POSITION, "\
                "valid values for POSITION are: 'left', 'right' and 'fullrow'"\
                % contents[0]
            )
        self.position = position
        self.fields = fields
        self.form_variable = form_variable

    def render(self, context):
        form = template.Variable(self.form_variable).resolve(context)
        new_form = copy.copy(form)
        new_form.fields = SortedDict(
            [(key, form.fields[key]) for key in self.fields]
        )

        class_name = {'left':    "first-tdfc",
                      'right':   "second-tdfc",
                      'fullrow': "full-tdfc"}[self.position]

        template_obj = get_template("txcommon/dual_forms.html")
        context = Context({'form': new_form, 'class_name': class_name})

        return template_obj.render(context)
