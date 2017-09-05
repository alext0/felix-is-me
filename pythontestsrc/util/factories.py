"""
Test data factories
"""

from datetime import datetime

import factory
from factory import Sequence

from util.test_base import TestBase


def subfactory(fty_name):
    return factory.SubFactory('factories.' + fty_name)


class BaseFty(TestBase):

    class Meta:
        abstract = True

    id = Sequence(lambda n:n)


class UserFty(BaseFty):
    class Meta:
        model = models.User

    created_at = datetime(2016, 1, 1, hour=1, minute=0, second=0)
    name = Sequence(lambda n: 'User{}'.format(n))
    email = factory.LazyAttribute(lambda o: (o.name + '@sainsburys.co.uk').lower())
