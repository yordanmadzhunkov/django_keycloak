from django.test import TestCase
from django.urls import reverse, resolve
from vei_platform.views.home import Home
from vei_platform.views.dashboard import Dashboard
from vei_platform.views.team import Team
from vei_platform.views.profile import MyProfileUpdate, Profile
from vei_platform.views.factory import FactoryCreate, FactoryEdit, FactoriesList, FactoryDetail, FactoriesForReview, CampaignCreate

class UrlTest(TestCase):
    def test_home_page_url(self):
        url = reverse('home')
        self.assertEquals(resolve(url).func.view_class, Home.as_view().view_class)

    def test_dashboard_page_url(self):
        url = reverse('dashboard')
        self.assertEquals(resolve(url).func.view_class, Dashboard.as_view().view_class)

    def test_my_profile_page_url(self):
        url = reverse('my_profile')
        self.assertEquals(resolve(url).func.view_class, MyProfileUpdate.as_view().view_class)

    def test_user_profile_page_url(self):
        url = reverse('user_profile', kwargs={'pk':2})
        self.assertEquals(resolve(url).func.view_class, Profile.as_view().view_class)

    def test_factory_create_page_url(self):
        url = reverse('factory_create')
        self.assertEquals(resolve(url).func.view_class, FactoryCreate.as_view().view_class)

    def test_factory_update_page_url(self):
        url = reverse('factory_edit', kwargs={'pk':2})
        self.assertEquals(resolve(url).func.view_class, FactoryEdit.as_view().view_class)

    def test_team_page_url(self):
        url = reverse('team')
        self.assertEquals(resolve(url).func.view_class, Team.as_view().view_class)
    
    def test_factories_with_campaigns_page_url(self):
        url = reverse('campaigns')
        self.assertEquals(resolve(url).func.view_class, FactoriesList.as_view().view_class)
    
    def test_factory_page_url(self):
        url = reverse('view_factory', kwargs={'pk':2})
        self.assertEquals(resolve(url).func.view_class, FactoryDetail.as_view().view_class)

    def test_factories_for_review_page_url(self):
        url = reverse('factories_for_review')
        self.assertEquals(resolve(url).func.view_class, FactoriesForReview.as_view().view_class)
        
    def test_factory_campaign_create_page_url(self):
        url = reverse('campaign_create', kwargs={'pk':2})
        self.assertEquals(resolve(url).func.view_class, CampaignCreate.as_view().view_class)
        