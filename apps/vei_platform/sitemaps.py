from django.contrib.sitemaps import Sitemap
from .models.factory import ElectricityFactory
 
 
class ElectricityFactorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return ElectricityFactory.objects.all()

    def lastmod(self, obj):
        return obj.updated_at
        
    #def location(self,obj):
    #    return '/blog/%s' % (obj.article_slug)
