import hashlib
import sys
from six import add_metaclass, string_types, integer_types
import ROOT as root, pyroot
from ROOT import RooFit

class _metavar(type):
	def __getattr__(cls, var):
		v = cls.get(var)
		if v is NotImplemented:
			return VarDummy(var)
		else:
			return v
	def __setattr__(cls, var, num):
		if var in cls.__dict__:
			super(_metavar, cls).__setattr__(var, num)
		else:
			cls.get(var).setVal(num)

class AutoNaming(object):
	_temp = 0
	@classmethod
	def _gen_name(cls):
		name = cls.__name__ + str(cls._temp)
		cls._temp += 1
		return name

class VarDummy:
	__slots__ = ('var_name',)
	def __init__(self, var_name):
		self.var_name = var_name
	def __call__(self, *args, **kwargs):
		return Var(self.var_name, *args, **kwargs)

@add_metaclass(_metavar)
class Var(AutoNaming):
	_MAX = 1000000.
	_INIT = 1.
	_dct = {}
	def __init__(self, name=None, *args, init=None):
		if init is None:
			init = self._INIT
		if name is None:
			name_r = name = self._gen_name
			self.var = root.RooRealVar.__init__(name, name, init, -self._MAX, self._MAX)
		elif isinstance(name, root.RooRealVar):
			self.var = name
			name_r = name.getTitle()
		elif isinstance(name, (integer_types, float)):
			name_r = self._gen_name
			self.var = root.RooRealVar.__init__(name_r, name_r, name, *args)
		elif isinstance(name, string_types):
			name_r = name
			self.var = root.RooRealVar.__init__(name, name, *args)
		else:
			raise TypeError
		Var._dct[name_r] = self
	def __getattr__(self, name):
		return self.var.__getattribute__(name)
	def __float__(self):
		return self.var.getVal()
	def __lshift__(self, num):
		self.var.setVal(num)
	def __and__(self, bl):
		self.var.setConstant(bool(bl))
	def __mul__(self, other):
		if isinstance(other, Pdf):
			return ExtendedPdf(((self, other),))
		return NotImplemented
	def __rsub__(self, num):
		if isinstance(name, (integer_types, float)):
			name = Var._gen_name()
			return root.RooFormulaVar(name, name, "{0} - {1}".format(num, self.var.getTitle()), root.RooArgList(self.var))
		else:
			return NotImplemented
	@classmethod
	def get(cls, name):
		if name in cls._dct:
			return cls._dct[name]
		else:
			raise KeyError
	@staticmethod
	def get_tuple(name):
		if name.startswith('__'):
			i = name.find('__', 2)
			if i == -1:
				raise ValueError('Var tuple Format Error')
			sep = name[:i + 2]
			name = name[i + 2:]
		else:
			sep = '__'
		names = name.split(sep)
		return VarTuple(Var._dct[c] for c in names)
	class _tuple:
		__slots__ = ()
		def __getattr__(self, name):
			return Var.get_tuple(name)
		def __setattr__(self, name, val):
			Var.get_tuple(name).setVal(val)
	tuple = _tuple()
	def frame(self, bins=None, *args, **kwargs):
		args = list(args)
		if type(bins) is int:
			args.append(root.RooFit.Bins(bins))
		elif bins is not None:
			args = [bins] + args
		return self.var.frame(*args)
	def ArgSet(self):
		return root.RooArgSet(self.var)

class VarTuple(tuple):
	def __new__(cls, *args, **kwargs):
		return super(VarTuple, cls).__new__(cls, tuple(*args, **kwargs))
	def __lshift__(self, t):
		self.setVal(t)
	def __and__(self, t):
		if isinstance(t, bool):
			for var in self:
				var & t
		else:
			if len(self) != len(t):
				raise IndexError(t)
			for var, num in zip(self, t):
				var & num
	def getVal(self):
		return tuple(x.getVal() for x in self)
	def setVal(self, t):
		if len(self) != len(t):
			raise IndexError(t)
		for var, num in zip(self, t):
			var.var.setVal(num)

class AllPdf(object):
	def __init__(self, pdf):
		self.pdf = pdf

class ExtendedPdf:
	def __init__(self, t):
		self.pair = list(t)
	def __add__(self, other):
		return ExtendedPdf(self.pair + other.pair)
	def __iadd__(self, other):
		self.pair.extend(other.pair)
		return self

class Add(AllPdf, AutoNaming):
	def __init__(self, *args):
		if len(args) != 0 and isinstance(args[0], ExtendedPdf):
			if len(args) >= 2 and type(args[1]) == str:
				name = args[1]
			else:
				name = self._gen_name
			var = [x[0].var for x in args[0].pair]
			pdfs = [x[1].pdf for x in args[0].pair]
			super(Add, self).__init__(root.RooAddPdf(name, name, root.RooArgList(*pdfs), root.RooArgList(*var)))
		else:
			raise TypeError(args)
	def __getattr__(self, name):
		return self.pdf.__getattribute__(name)
	def __getitem__(self, index):
		return AddPdfItem(self, index)

class AddPdfItem(object):
	def __init__(self, add, index):
		self.pdf = add
		if isinstance(index, string_types):
			self.index = index
		elif isinstance(index, tuple):
			self.index = ','.join(index)
		else:
			raise TypeError
	def plotOn(self, frame, *args):
		return self.pdf.plotOn(frame, root.RooFit.Components(self.index), root.RooFit.Name(self.index), *args)


class Pdf:
	pass
