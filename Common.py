class Common(object):
	_graph = None
	_initialized = False
	_mystery = None
	_mystery_correct = None

	@classmethod
	def graph(cls):
		return cls._graph
	
	@classmethod
	def setGraph(cls, graph):
		cls._graph = graph

	@classmethod
	def initialized(cls):
		return cls._initialized
	
	@classmethod
	def setInitialized(cls, init):
		cls._initialized = init

	@classmethod
	def mystery(cls):
		return cls._mystery

	@classmethod
	def setMystery(cls, mys):
		cls._mystery = mys

	@classmethod
	def mystery_correct(cls):
		return cls._mystery_correct

	@classmethod
	def setMystery_Correct(cls, mys):
		cls._mystery_correct = mys
