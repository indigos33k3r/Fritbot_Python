import datetime

from twisted.internet import defer, reactor

import config
from db import db

class Route(object):
    '''A valid route for sending messages. Currently, this could be a room or a user.'''

    TYPE = "None"
    '''What type of route this is. Should be changed by subclasses.'''

    uid = None
    '''Unique identifier for this route.'''

    info = {}
    '''MongoDB Information for this route.'''

    _collection = None
    '''MongoDB Collection representing all objects for this route type.'''
    
    def __getitem__(self, key):
        '''Getter for contained MongoDB info object. Returns None if key is not found.'''
        if key in self.info:
            return self.info[key]
        else:
            return None

    def __setitem__(self, key, value):
        '''Setter for contained MongoDB info object.'''
        self.info[key] = value

    def __init__(self, uid):
        '''Initialize a route with given unique identifier.'''
        self.uid = uid
        self.refresh()

    def __repr__(self):
        return "<{0} {1}>".format(self.TYPE, self.uid)

    def send(self, message, delay=False):
        '''Attempt to send a message with given delay'''
        time = 0.2
        if delay:
            time = random.random() + 2.0
        print "Sending <{0}>: {1}".format(self.uid, message)            
        reactor.callLater(time, self._send, message)

    def _send(self, message):
        '''Template to actually send a message via this route. Must be implemented in a subclass.'''
        raise NotImplementedError("_send() is not implemented in this Route instance.")

    def refresh(self):
        '''Template to refresh the mongodb information for this route. Must be implemented in a subclass.'''
        raise NotImplementedError("refresh() is not implemented in this Route instance.")

    def save(self):
        '''Save the MongoDB info for this route.'''
        if self._collection is not None:
            self._collection.save(self.info)
        else:
            raise NotImplementedError("save() cannot be run when _collection is not set. It should be set by the subclass.")

class Room(Route):

    TYPE = "Room"

    roster = {}
    '''Dict of User objects currently in this room, by uid'''

    undostack = []
    '''Undo stack for this room.'''

    def __init__(self, uid, nick=config.CONFIG["name"]):
        self['nick'] = nick
        self._collection = db.db.rooms
        Route.__init__(self, uid)

    def refresh(self):
        #TODO: Implement time locks, if I care.
        print "Refreshing configuration for room: " + self.uid
        mdbRoom = db.db.rooms.find_one({"name": self.uid})

        if mdbRoom is None:
            print "Not found, creating new room in DB."
            mdbRoom = {
                "name": self.uid,
                "nick": self['nick'],
                "auths": ["core"]
            }
            
            db.db.rooms.insert(mdbRoom)

        if "squelched" in self.info and self["squelched"] > datetime.datetime.now():
            seconds = (self["squelched"] - datetime.datetime.now()).seconds
            minutes = int(seconds / 60)
            seconds = seconds - (minutes * 60)
            if minutes > 0:
                self.squelched = "{0} minute(s)".format(minutes)
            else:
                self.squelched = "{0} second(s)".format(seconds)
        else:
            self.squelched = False

        self.info = mdbRoom
    
    def addUndo(self, undo):
        self.undostack.append(undo)

    def setNick(self, nick):
        raise NotImplementedError("setNick() must be implemented by a sub-class.")

class User(Route):

    TYPE = "User"

    undostack = []
    '''Undo stack for this user.'''

    def __init__(self, uid, nick):
        self['nick'] = nick
        self._collection = db.db.users
        Route.__init__(self, uid)

    def refresh(self):
        print "Refreshing configuration for user: " + self.uid
        mdbUser= db.db.users.find_one({"resource": self.uid})

        if mdbUser is None:
            print "Not found, creating new user in DB."
            mdbUser = {
                "resource": self.uid,
                "nick": self['nick']
            }
            
            db.db.rooms.insert(mdbUser)

        self.info = mdbUser 

class Interface(object):
    
    bot = None

    def __init__(self, bot):
        self.bot = bot
        bot.registerInterface(self)

    def doNickUpdate(self, user, room, nick):
        '''Update user and room nicknames, if appropriate.
        Helper function that should be called by sub-classes whenever a new user connects to a room, or a user of a room changes nicknames.'''

        if "nicks" in user.info:
            found = False
            for r in user["nicks"]:
                if r["room"] == room.uid:
                    if nick not in r["nicks"]:
                        r["nicks"].append(nick)
                    found = True
                    break
            if not found:
                user["nicks"].append({"room": room.uid, "nicks": [nick]})
        else:
            user["nicks"] = [{"room": room.uid, "nicks": [user['nick']]}]

        if "nick" not in user.info:
            user["nick"] = user.nick

        user.save()

    def joinRoom(self, room, nick):
        raise NotImplementedError("joinRoom() must be implemented by a sub-class.")

    def leaveRoom(self, room, nick):
        raise NotImplementedError("leaveRoom() must be implemented by a sub-class.")