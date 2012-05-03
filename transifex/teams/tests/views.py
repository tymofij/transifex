import mock

from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User

import simplejson

from languages.models import Language
from transifex.teams.models import TeamRequest, TeamAccessRequest
from transifex.teams.models import Team
import transifex.teams.views
from txcommon.tests import base, utils


class TestTeams(base.BaseTestCase):

    def setUp(self):
        super(TestTeams, self).setUp()

    def test_team_list(self):
        url = reverse('project_detail', args=[self.project.slug])
        resp = self.client['registered'].get(url)
        self.assertContains(resp, '(pt_BR)', status_code=200)

    def test_team_details(self):
        url = reverse('team_detail', args=[self.project.slug, self.language.code])
        resp = self.client['registered'].get(url)
        self.assertContains(resp, '(Brazil)', status_code=200)

    def test_create_team(self):
        """Test a successful team creation."""
        url = reverse('team_create', args=[self.project.slug])
        DATA = {
            'language': self.language_ar.id,
            'project': self.project.id,
            'coordinators': '|%s|' % User.objects.all()[0].id,
            'members': '|',
        }
        resp = self.client['maintainer'].post(url, data=DATA, follow=True)
        #from ipdb import set_trace; set_trace()
        #self.response_in_browser(resp)
        self.assertTemplateUsed(resp, 'teams/team_members.html')
        self.assertEqual(resp.context['team'].project.id, self.project.id)
        self.assertEqual(resp.context['team'].language.id, self.language_ar.id)
        self.assertIn(User.objects.all()[0], resp.context['team'].coordinators.all())

    def team_details_release(self):
        """Test releases appear correctly on team details page."""
        self.assertTrue(self.project.teams.all().count())
        url = reverse('team_detail', args=[self.project.slug, self.language.code])
        resp = self.client['team_member'].get(url)
        self.assertContains(resp, 'releaseslug', status_code=200)

    def test_team_request(self, lang_code=None):
        """Test creation of a team request"""
        url = reverse('team_request', args=[self.project.slug])
        if lang_code != None:
            language = Language.objects.get(code='ar')
        else:
            language = self.language_ar
        resp = self.client['registered'].post(url,
            {'language':language.id}, follow=True)
        self.assertContains(resp, "You requested creation of the &#39;%s&#39; team."%(language.name))
        self.assertEqual(resp.status_code, 200)

    def test_team_requests_on_team_creation(self):
        #test team request after a team is created
        language = self.language_ar
        url = reverse('team_request', args=[self.project.slug])
        self.test_team_request()
        self.test_create_team()
        self.assertTrue(TeamAccessRequest.objects.get(user=self.user[
            'registered'], team__project=self.project,
            team__language=self.language_ar))
        self.assertFalse(TeamRequest.objects.filter(user=self.user[
            'registered'], project=self.project))

        Team.objects.get(project=self.project,
                language=self.language_ar).delete()

        resp = self.client['registered'].post(url,
            {'language':language.id}, follow=True)
        self.assertContains(resp, "You requested creation of the &#39;%s&#39; team."%(language.name))
        self.assertEqual(resp.status_code, 200)

        url = reverse('team_create', args=[self.project.slug])
        DATA = {
            'language': self.language_ar.id,
            'project': self.project.id,
            'coordinators': '|%s|' % User.objects.all()[0].id,
            'members': '|%s|' % self.user['registered'].id,
        }
        resp = self.client['maintainer'].post(url, data=DATA, follow=True)
        self.assertTemplateUsed(resp, 'teams/team_members.html')
        self.assertEqual(resp.context['team'].project.id, self.project.id)
        self.assertEqual(resp.context['team'].language.id, self.language_ar.id)
        self.assertIn(User.objects.all()[0], resp.context['team'].coordinators.all())
        self.assertFalse(TeamAccessRequest.objects.filter(user=self.user[
            'registered'], team__project=self.project,
            team__language=self.language_ar))
        self.assertFalse(TeamRequest.objects.filter(user=self.user[
            'registered'], project=self.project))

    def test_team_request_deny(self):
        """Test denial of a team request"""
        self.test_team_request()
        language = self.language_ar
        url = reverse('team_request_deny', args=[self.project.slug, language.code])
        resp = self.client['maintainer'].post(url, {"team_request_deny":"Deny"}, follow=True)
        self.assertContains(resp, 'You rejected the request by', status_code=200)

    def test_team_request_approve(self):
        """Test approval of a team request"""
        self.test_team_request()
        url = reverse('team_request_approve', args=[self.project.slug, self.language_ar.code])
        resp = self.client['maintainer'].post(url, {'team_request_approve':'Approve'}, follow=True)
        self.assertContains(resp, 'You approved the', status_code=200)

    def test_team_join_request(self):
        """Test joining request to a team"""
        url = reverse('team_join_request', args=[self.project.slug, self.language.code])
        resp = self.client['registered'].post(url, follow=True)
        self.assertContains(resp, 'You requested to join the', status_code=200)

    def test_team_join_withdraw(self):
        """Test the withdrawal of a team join request by the user"""
        self.test_team_join_request()
        url = reverse('team_join_withdraw', args=[self.project.slug, self.language.code])
        resp = self.client['registered'].post(url, follow=True)
        self.assertContains(resp, 'You withdrew your request to join the', status_code=200)

    def test_team_leave(self):
        """Test leaving a team"""
        self.team.members.add(self.user['registered'])
        url = reverse('team_leave', args=[self.project.slug, self.language.code])
        resp = self.client['registered'].post(url, follow=True)
        self.assertContains(resp, 'You left the', status_code=200)

    def test_team_delete(self):
        """Test team delete """
        self.test_create_team()
        url = reverse('team_delete', args=[self.project.slug, self.language_ar.code])
        resp = self.client['maintainer'].post(url, follow=True)
        self.assertContains(resp, 'was deleted', status_code=200)

class TestTeamJoinApprove(base.BaseTestCase):

    def setUp(self):
        super(TestTeamJoinApprove, self).setUp()
        self.request = mock.MagicMock(name="request",
            user=self.user['team_coordinator'], method="POST")
        self.request.is_ajax.return_value = True

    @mock.patch('transifex.teams.views.HttpResponseRedirect')
    def test_proceeds_only_if_ajax_post(self, mock_redirect):
        self.request.is_ajax.return_value = False

        transifex.teams.views.team_join_approve(self.request,
            project_slug=self.project.slug,
            language_code=self.language.code,
            username='registered')

        mock_redirect.assert_called_once_with(reverse("team_detail",
            args=[self.project.slug, self.language.code]))

    def test_approves_if_everything_ok(self):
        TeamAccessRequest(team=self.team, user=self.user['registered']).save()

        resp = transifex.teams.views.team_join_approve(self.request,
                    project_slug=self.project.slug,
                    language_code=self.language.code,
                    username='registered')

        self.assertDictEqual({
            'user_id': self.user['registered'].id,
            'success': True,
            'accepted': True
        }, simplejson.loads(resp.content))

class TestTeamJoinDeny(base.BaseTestCase):

    def setUp(self):
        super(TestTeamJoinDeny, self).setUp()
        self.request = mock.MagicMock(name="request",
            user=self.user['team_coordinator'], method="POST")
        self.request.is_ajax.return_value = True

    @mock.patch('transifex.teams.views.HttpResponseRedirect')
    def test_proceeds_only_if_ajax_post(self, mock_redirect):
        self.request.is_ajax.return_value = False

        transifex.teams.views.team_join_deny(self.request,
            project_slug=self.project.slug,
            language_code=self.language.code,
            username='registered')

        mock_redirect.assert_called_once_with(reverse("team_detail",
            args=[self.project.slug, self.language.code]))

    def test_denies_if_everything_ok(self):
        TeamAccessRequest(team=self.team, user=self.user['registered']).save()

        resp = transifex.teams.views.team_join_deny(self.request,
                    project_slug=self.project.slug,
                    language_code=self.language.code,
                    username='registered')

        self.assertDictEqual({
            'user_id': self.user['registered'].id,
            'success': True,
            'accepted': False,
        }, simplejson.loads(resp.content))

class TestConvertMembershipType(base.BaseTestCase):

    def setUp(self):
        super(TestConvertMembershipType, self).setUp()
        self.request = mock.MagicMock(name="request",
            user=self.user['team_coordinator'], method="POST")

    def test_convert_reviewer_to_coordinator(self):
        self.team.reviewers.add(self.user['registered'])

        resp = transifex.teams.views.convert_membership_type(self.request,
            project_slug=self.project.slug,
            language_code=self.language.code,
            username='registered',
            member_type='coordinator')

        self.assertIn(self.user['registered'], self.team.coordinators.all())
        self.assertNotIn(self.user['registered'], self.team.members.all())
        self.assertNotIn(self.user['registered'], self.team.reviewers.all())
        self.assertDictEqual({'success': True}, simplejson.loads(resp.content))

    def test_convert_translator_to_reviewer(self):
        self.team.reviewers.add(self.user['registered'])

        resp = transifex.teams.views.convert_membership_type(self.request,
            project_slug=self.project.slug,
            language_code=self.language.code,
            username='registered',
            member_type='reviewer')

        self.assertIn(self.user['registered'], self.team.reviewers.all())
        self.assertNotIn(self.user['registered'], self.team.coordinators.all())
        self.assertNotIn(self.user['registered'], self.team.members.all())
        self.assertDictEqual({'success': True}, simplejson.loads(resp.content))

    def test_member_to_invalid_membership_type(self):
        self.team.reviewers.add(self.user['registered'])

        resp = transifex.teams.views.convert_membership_type(self.request,
            project_slug=self.project.slug,
            language_code=self.language.code,
            username='registered',
            member_type='still_being')

        self.assertDictEqual({'success': False}, simplejson.loads(resp.content))

class TestTeamMembersCommonContext(base.BaseTestCase):

    def setUp(self):
        super(TestTeamMembersCommonContext, self).setUp()

    def test_common_context_without_username(self):
        request = mock.MagicMock(name="request",
            user=self.user['registered'], method="GET")

        res = transifex.teams.views._team_members_common_context(request,
            project_slug=self.project.slug,
            language_code=self.language.code)

        self.assertDictContainsSubset({
            'project': self.project,
            'language': self.language,
            'team': self.team,
            'project_team_members': True,
            'can_coordinate': False,
        }, res)

    def test_common_context_with_username(self):
        request = mock.MagicMock(name="request",
            user=self.user['team_coordinator'],
            method="GET",
            GET={'username': 'registered'})

        res = transifex.teams.views._team_members_common_context(request,
            project_slug=self.project.slug,
            language_code=self.language.code)

        self.assertDictContainsSubset({
            'project': self.project,
            'language': self.language,
            'team': self.team,
            'project_team_members': True,
            'can_coordinate': True,
        }, res)
