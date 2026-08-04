# -*- coding: utf-8 -*-

# Order matters: handlers/ must be imported before models/ and
# services/, since loyalty_program.py's compute method and
# social_loyalty_config.py both introspect the handler registry, and
# services/ imports directly from handlers/.
from . import handlers
from . import services
from . import controllers
from . import models
