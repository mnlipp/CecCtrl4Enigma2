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
from circuits.core.pollers import BasePoller
from twisted.internet import reactor
from zope.interface.declarations import implementer
from twisted.internet.interfaces import IReadDescriptor, IWriteDescriptor


class TwistedPoller(BasePoller):

    channel = "twisted"

    def __init__(self, channel=channel):
        super(TwistedPoller, self).__init__(channel=channel)
        
        self._readDescs = []
        self._writeDescs = []
        self._pending = []
        reactor.addReader(CtrlReaderDescriptor(self, self._ctrl_recv))

    def _pending_read(self, rd):
        self._pending.append(rd)

    def _pending_wite(self, wd):
        self._pending.append(wd)

    def addReader(self, source, fd):
        channel = getattr(source, "channel", "*")
        rd = ReaderDescriptor(self, fd, channel)
        self._readDescs.append(rd)
        reactor.addReader(rd)

    def addWriter(self, source, fd):
        channel = getattr(source, "channel", "*")
        wr = WriterDescriptor(self, fd, channel)
        self._writeDescs.append(wr)
        reactor.addWriter(wr)

    def removeReader(self, fd):
        for rd in self._readDescs:
            if rd.fileno() == fd:
                self._readDescs.remove(rd)
                reactor.removeReader(rd)

    def removeWriter(self, fd):
        for wr in self._writeDescs:
            if wr.fileno() == fd:
                self._writeDescs.remove(wr)
                reactor.removeWriter(wr)

    def isReading(self, fd):
        for rd in self._readDescs:
            if rd.fileno() == fd:
                return True
        return False

    def isWriting(self, fd):
        for wr in self._writeDescs:
            if wr.fileno() == fd:
                return True
        return False

    def discard(self, fd):
        self.removeReader(fd)
        self.removeWriter(fd)

    def getTarget(self, fd):
        for rd in self._readDescs:
            if rd.fileno() == fd:
                return rd._channel
        for wr in self._writeDescs:
            if wr.fileno() == fd:
                return wr._channel


    def _generate_events(self, event):
        try:
            if not any(self._pending):
                return
            timeout = event.time_left
            if timeout < 0:
                r, w, _ = select.select(self._read, self._write, [])
            else:
                r, w, _ = select.select(self._read, self._write, [], timeout)
        except (SelectError, SocketError, IOError) as e:
            # select(2) encountered an error
            if e.args[0] in (0, 2):
                # windows does this if it got an empty list
                if (not self._read) and (not self._write):
                    return
                else:
                    raise
            elif e.args[0] == EINTR:
                return
            elif e.args[0] == EBADF:
                return self._preenDescriptors()
            else:
                # OK, I really don't know what's going on.  Blow up.
                raise

        for sock in w:
            if self.isWriting(sock):
                self.fire(_write(sock), self.getTarget(sock))

        for sock in r:
            if sock == self._ctrl_recv:
                self._read_ctrl()
                continue
            if self.isReading(sock):
                self.fire(_read(sock), self.getTarget(sock))


@implementer(IReadDescriptor)
class CtrlReaderDescriptor(object):
    def __init__(self, poller, fd):
        self._poller = poller
        self._fd = fd

    def logPrefix(self):
        return "CircuitsCtrlReader"

    def fileno(self):
        return self._fd.fileno()

    def connectionLost(self, reason):
        self._fd.close()

    def doRead(self):
        self._poller._read_ctrl()

@implementer(IReadDescriptor)
class ReaderDescriptor(object):
    def __init__(self, poller, fd, target):
        self._poller = poller
        self._fd = fd
        self._target = target

    def logPrefix(self):
        return "CircuitsReader"

    def fileno(self):
        return self._fd.fileno()

    def connectionLost(self, reason):
        self._fd.close()

    def doRead(self):
        self._poller._pending_read(self)


@implementer(IWriteDescriptor)
class WriterDescriptor(object):
    def __init__(self, poller, fd, target):
        self._poller = poller
        self._fd = fd
        self._target = target

    def logPrefix(self):
        return "Writer"

    def fileno(self):
        return self._fd.fileno()

    def connectionLost(self, reason):
        self._fd.close()

    def doWrite(self):
        self._poller._pending_write(self)

