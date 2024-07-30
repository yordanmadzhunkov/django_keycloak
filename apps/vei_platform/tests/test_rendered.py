from django.test import TestCase

from django.template.loader import render_to_string

from vei_platform.settings.base import BASE_DIR


class ProjectTests(TestCase):
    def render_and_compare(self, context, template_name, ref_file_name):
        content = render_to_string(template_name, context)
        try:
            with open(ref_file_name, "r") as reference_file:
                ref = reference_file.read()
                self.assertEqual(ref, content)
        except FileNotFoundError:
            with open(ref_file_name, "w") as reference_file:
                reference_file.write(content)
                self.assertTrue(False, "Writing to disk ref file = %s " % ref_file_name)

    def test_render_electricity_prices_0(self):
        self.render_and_compare(
            context={"some_key": "some_value"},
            template_name=BASE_DIR / "templates/electricity_prices.html",
            ref_file_name=BASE_DIR / "static_to_collect/electricity_prices_0.html",
        )
