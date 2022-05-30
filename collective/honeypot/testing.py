# -*- coding: utf-8 -*-

from Acquisition import aq_base
from plone.app.discussion.interfaces import IDiscussionSettings
from plone.app.testing import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.registry.interfaces import IRegistry
from plone.testing import zope
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from zope.component import getSiteManager
from zope.component import queryUtility

import collective.honeypot.config


# We want WHITELISTED_START to be empty by default currently, but we
# do want to test it.
start = list(collective.honeypot.config.WHITELISTED_START)
start.append("jq_")
collective.honeypot.config.WHITELISTED_START = set(start)


def patch_mailhost(portal):
    registry = queryUtility(IRegistry)
    registry["plone.email_from_address"] = "webmaster@example.org"
    portal._original_MailHost = portal.MailHost
    portal.MailHost = mailhost = MockMailHost("MailHost")
    mailhost.smtp_host = "localhost"
    sm = getSiteManager(context=portal)
    sm.unregisterUtility(provided=IMailHost)
    sm.registerUtility(mailhost, provided=IMailHost)


def unpatch_mailhost(portal):
    portal.MailHost = portal._original_MailHost
    sm = getSiteManager(context=portal)
    sm.unregisterUtility(provided=IMailHost)
    sm.registerUtility(aq_base(portal._original_MailHost), provided=IMailHost)


class BasicFixture(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.honeypot

        self.loadZCML(package=collective.honeypot)
        # Install product and call its initialize() function
        zope.installProduct(app, "collective.honeypot")

    def tearDownZope(self, app):
        # Uninstall product
        zope.uninstallProduct(app, "collective.honeypot")

    def setUpPloneSite(self, portal):
        patch_mailhost(portal)
        # Enable commenting, self registration, and sending mail.
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IDiscussionSettings)
        settings.globally_enabled = True
        settings.anonymous_comments = True
        portal.manage_permission("Reply to item", ("Anonymous", "Manager"))
        portal.manage_permission("Allow sendto", ("Anonymous", "Manager"))
        portal.manage_permission("Add portal member", ("Anonymous", "Manager"))

    def teardownPloneSite(self, portal):
        unpatch_mailhost(portal)


class FixesFixture(BasicFixture):
    # Fixture that loads fixes.zcml.  This activates the improved
    # templates and scripts.
    defaultBases = (PLONE_FIXTURE,)
    load_fixes = True

    def setUpZope(self, app, configurationContext):
        super(FixesFixture, self).setUpZope(app, configurationContext)
        # Load extra ZCML.
        import collective.honeypot

        self.loadZCML(package=collective.honeypot, name="fixes.zcml")


BASIC_FIXTURE = BasicFixture()
FIXES_FIXTURE = FixesFixture()
BASIC_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BASIC_FIXTURE,), name="collective.honeypot:BasicFunctional",
)
FIXES_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXES_FIXTURE,), name="collective.honeypot:FixesFunctional",
)
