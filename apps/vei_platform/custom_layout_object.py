from crispy_forms.layout import LayoutObject, TEMPLATE_PACK
from django.shortcuts import render
from django.template.loader import render_to_string

class Formset(LayoutObject):
    template = "snippets/formset.html"

    def __init__(self, formset_name_in_context, helper_context_name=None, template=None):
        self.formset_name_in_context = formset_name_in_context
        self.helper_context_name = helper_context_name 
        self.fields = []
        if template:
            self.template = template

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        formset = context[self.formset_name_in_context]
        helper = context.get(self.helper_context_name)
        return render_to_string(self.template, {'formset': formset, 'helper': helper})


