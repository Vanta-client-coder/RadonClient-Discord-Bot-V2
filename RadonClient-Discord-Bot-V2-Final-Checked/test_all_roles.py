import unittest
from types import SimpleNamespace
from core.permissions import command_allowed

ROLES={"owner":"1555224034902278214", "coOwner":"1555224142792491128", "dev":"1555223821227917343", "team":"1554869329684725812", "autoRole":"1555309234776711168", "support":["1555224377652416532"]}

def member(*ids):
    return SimpleNamespace(roles=[SimpleNamespace(id=int(i)) for i in ids])

class RoleTests(unittest.TestCase):
    def setUp(self): self.cfg={"roles":ROLES,"commandAccess":{}}
    def m(self, name):
        value=ROLES[name]
        return member(*(value if isinstance(value,list) else [value]))
    def test_public_all(self):
        for role in [member(),*(self.m(x) for x in ROLES)]:
            for cmd in ('help','ping','userinfo','membercount','serverinfo'):
                self.assertTrue(command_allowed(role,cmd,self.cfg),(role,cmd))
    def test_owners_everything(self):
        for key in ('owner','coOwner'):
            for cmd in ('ban','announce','giveaway','ticketpanel','dm'):
                self.assertTrue(command_allowed(self.m(key),cmd,self.cfg))
    def test_developer(self):
        self.assertTrue(command_allowed(self.m('dev'),'ban',self.cfg))
        self.assertFalse(command_allowed(self.m('dev'),'announce',self.cfg))
    def test_team(self):
        self.assertTrue(command_allowed(self.m('team'),'timeout',self.cfg))
        self.assertFalse(command_allowed(self.m('team'),'ban',self.cfg))
    def test_support(self):
        self.assertTrue(command_allowed(self.m('support'),'claim',self.cfg))
        self.assertFalse(command_allowed(self.m('support'),'kick',self.cfg))
    def test_autorole(self):
        self.assertFalse(command_allowed(self.m('autoRole'),'ban',self.cfg))
    def test_unknown_role(self):
        self.assertFalse(command_allowed(member('555555555555555555'),'claim',self.cfg))
    def test_explicit_denial(self):
        self.cfg['commandAccess']={'dev':[]}
        self.assertFalse(command_allowed(self.m('dev'),'ban',self.cfg))
    def test_custom_access(self):
        self.cfg['commandAccess']={'support':['giveaway']}
        self.assertTrue(command_allowed(self.m('support'),'giveaway',self.cfg))
        self.assertFalse(command_allowed(self.m('support'),'claim',self.cfg))
    def test_combined_roles(self):
        self.assertTrue(command_allowed(member(ROLES['team'], ROLES['support'][0]),'claim',self.cfg))
        self.assertFalse(command_allowed(member(ROLES['team'], ROLES['support'][0]),'ban',self.cfg))

if __name__=='__main__': unittest.main()
