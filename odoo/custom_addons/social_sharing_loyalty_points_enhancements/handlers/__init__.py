# -*- coding: utf-8 -*-
"""
Importing this package registers every built-in reward handler with the
central registry (see registry.py). Order does not matter functionally,
but is kept alphabetical/grouped for readability.

To add a new reward type, create the new handler module and add its
import here - nothing else in this package needs to change.
"""

from . import base_handler
from . import registry
from . import share_base
from . import referral_base

from . import product_share
from . import blog_share
from . import event_share

from . import event_referral
from . import product_referral
from . import blog_referral

from . import customer_signup
