"""
..
   This file is part of the circuits minimal portal component.
   Copyright (C) 2012-2015 Michael N. Lipp
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. moduleauthor:: mnl
"""
from circuits.web.controllers import BaseController
from circuits.web.errors import httperror

import os
import sys, traceback
import mimetypes
import tenjin
from tenjin.helpers import *

class TemplateController(BaseController):

    def __init__(self, templates_dir, *args, **kwargs):
        super(TemplateController, self).__init__(*args, **kwargs)
        self._engine = tenjin.Engine(path=templates_dir)

    def serve_tenjin(self, request, response, path, context, 
                     content_type="text/html", disposition=None, name=None,
                     engine=None, globexts=None):
        return serve_tenjin(engine or self._engine, request, response, path, 
                            context, content_type, disposition, name, globexts)

def serve_tenjin(engine, request, response, path, context, 
                 content_type=None, disposition=None, name=None, globexts=None):
    if not engine and not os.path.isabs(path):
        raise ValueError("'%s' is not an absolute path." % path)

    if content_type is None:
        # Set content-type based on filename extension
        content_type, _ = mimetypes.guess_type(path, False)
        if content_type is None:
            content_type = "text/plain"
    response.headers['Content-Type'] = content_type

    if disposition is not None:
        if name is None:
            name = os.path.basename(path)
        cd = '%s; filename="%s"' % (disposition, name)
        response.headers["Content-Disposition"] = cd

    if globexts:
        globs = tenjin.helpers.__dict__.copy()
        globs.update(globexts)
    else:
        globs = tenjin.helpers.__dict__
    #tenjin.helpers.

    try:
        response.body = engine.render(path, context, globals = globs)
    except Exception as error:
        etype, evalue, etraceback = sys.exc_info()
        error = (etype, evalue, traceback.format_tb(etraceback))
        return httperror(request, response, 500, error=error)        
    return response
