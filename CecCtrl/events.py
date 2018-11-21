"""
..
   This file is part of the CEC Control plugin.
   Copyright (C) 2018 Michael N. Lipp
   
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
from datetime import datetime
from circuits.core.events import Event

class cec_read(Event):
    
    def __init__(self, msg, *args, **kwargs):
        super(cec_read, self).__init__(*args, **kwargs)
        self.timestamp = datetime.now()
        self.msg = msg
    
class cec_write(Event):
    
    def __init__(self, msg, *args, **kwargs):
        super(cec_write, self).__init__(*args, **kwargs)
        self.msg = msg
