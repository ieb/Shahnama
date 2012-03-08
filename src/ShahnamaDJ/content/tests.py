'''
Created on Jan 10, 2012

@author: ieb
'''
from django.test import TestCase
from ShahnamaDJ.content.models import ContentMeta, Content
from django.test.client import Client
class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class PageIntegrationTest(TestCase):
    fixtures = ['contenttest.json']
    
    def test_Pages(self):
        print "testing pages"
        c = Client()
        for contentObject in Content.objects.all():
            response = c.get("/page/%s" % (contentObject.id))
            self.assertEqual(200,response.status_code)
            print "Loaded Page /page/%s got %s %s" % (contentObject.id, response.status_code, len(response.content))
