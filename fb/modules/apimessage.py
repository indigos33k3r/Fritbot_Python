from fb.api.core import api
from fb.api.util import returnjson, APIResponse
from fb.modules.base import Module
from fb.api.simple import SimpleFunction
from fb.api.core import api
from fb.api import security

class APIMessageResponse(APIResponse):

	def __init__(self):
		APIResponse.__init__(self)
		self.putChild('room', SimpleFunction(self.room_message))
		self.putChild('user', SimpleFunction(self.user_message))

	@returnjson
	def room_message(self, request):
		if 'key' in request.args:
			data = security.getKeyInfo(request.args['key'][0])
			if data is None:
				return self.error(request, self.UNAUTHORIZED)
		else:
			return self.error(request, self.UNAUTHORIZED)

		if not 'id' in request.args:
			return self.error(request, 400, "Room id not specified.")
		if not 'message' in request.args:
			return self.error(request, 400, "Message not specified.")

		room = api.bot.getRoom(request.args['id'][0]);
		if room is None:
			return self.error(request, 400, "Bot is not in that room.")

		room.send(request.args['message'][0])

		return {'state': 'Message sent.'}

	@returnjson
	def user_message(self, request):
		if 'key' in request.args:
			data = security.getKeyInfo(request.args['key'][0])
			if data is None:
				return self.error(request, self.UNAUTHORIZED)
		else:
			return self.error(request, self.UNAUTHORIZED)

		if not 'id' in request.args:
			return self.error(request, 400, "User id not specified.")
		if not 'message' in request.args:
			return self.error(request, 400, "Message not specified.")

		user = api.bot.getUser(request.args['id'][0]);
		if user is None:
			return self.error(request, 400, "Bot cannot talk to that user.")

		user.send(request.args['message'][0])

		return {'state': 'Message sent.'}

class APIMessageModule(Module):
	
	uid="apimessage"
	name="API Messaging Service"
	description="Simple messaging service to allow external programs to direct the bot to message users or rooms."
	author="Michael Pratt (michael.pratt@bazaarvoice.com)"

	apis = {
		"message": APIMessageResponse()
	}

module = APIMessageModule
