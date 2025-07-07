import hashlib
import sys
from six import add_metaclass, string_types, integer_types
import ROOT as root
from ROOT import RooFit

URooVarTypes = (root.RooRealVar, root.RooFormulaVar)

class _metavar(type): # {{{
	def __getattr__(cls, var):
		v = cls.get(var)
		if v is NotImplemented:
			return VarDummy(var)
		else:
			return v
	def __setattr__(cls, var, num):
		for clsm in cls.__mro__:
			if var in clsm.__dict__:
				super(_metavar, cls).__setattr__(var, num)
				break
		else:
			cls.get(var).setVal(num)
# }}}

class AutoNaming(object): # {{{
	_temp = 0
	@classmethod
	def _gen_name(cls, use_name=None):
		use_name = use_name or cls.__name__
		name = use_name + str(cls._temp)
		cls._temp += 1
		return name
	@classmethod
	def _gen_names(cls, count, use_name=None):
		return tuple(cls._gen_name(use_name) for i in range(count))
# }}}

class VarDummy: # {{{
	__slots__ = ('var_name',)
	def __init__(self, var_name):
		self.var_name = var_name
	def __call__(self, *args, **kwargs):
		return Var(self.var_name, *args, **kwargs)
# }}}

@add_metaclass(_metavar)
class Var(AutoNaming): # {{{
	_MAX = 10000000.
	_INIT = 1.
	_dct = {}
	def __init__(self, name=None, *args, **kwargs):
		if 'init' in kwargs:
			_init = kwargs['init']
		else:
			_init = self._INIT
		if name is None:
			name_r = name = self._gen_name()
			self.var = root.RooRealVar(name, name, _init, -self._MAX, self._MAX)
		elif isinstance(name, string_types):
			name_r = name
			if len(args) == 0:
				self.var = root.RooRealVar(name, name, _init, -self._MAX, self._MAX)
			else:
				self.var = root.RooRealVar(name, name, *args)
		elif isinstance(name, (integer_types, float)):
			name_r = self._gen_name()
			self.var = root.RooRealVar(name_r, name_r, name, *args)
		elif isinstance(name, URooVarTypes):
			self.var = name
			name_r = name.GetName()
		else:
			raise TypeError
		if 'Print' in Var.__dict__:
			Var.Print(name_r)
		self.name = name_r
		Var._dct[name_r] = self
	def __getattr__(self, name):
		return self.var.__getattribute__(name)
	def __float__(self):
		return self.var.getVal()
	def __lshift__(self, num):
		self.var.setVal(num)
		return self
	def __and__(self, bl):
		self.var.setConstant(bool(bl))
		return self
	def __mul__(self, other):
		if isinstance(other, AllPdf):
			return ExtendedPdf(((self, other),))
		return NotImplemented
	def __rsub__(self, num):
		if isinstance(num, (integer_types, float)):
			name = self._gen_name()
			return root.RooFormulaVar(name, name, "{0} - {1}".format(num, self.var.getTitle()), root.RooArgList(self.var))
		else:
			return NotImplemented
	@classmethod
	def get(cls, name):
		if name in cls._dct:
			return cls._dct[name]
		else:
			return NotImplemented
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
	def ArgList(self):
		return root.RooArgList(self.var)
	def ArgSet(self):
		return root.RooArgSet(self.var)
# }}}
def _change(arg, init=False): # {{{
	if isinstance(arg, string_types):
		if arg in Var._dct:
			return Var._dct[arg]
		else:
			return Var(arg)
	elif isinstance(arg, URooVarTypes):
		return Var(arg)
	elif isinstance(arg, Var):
		return arg
	elif isinstance(arg, integer_types) or isinstance(arg, float):
		if init:
			return Var(init=arg)
		return Var(arg)
	else:
		raise TypeError(arg)
# }}}

VarList_cache = []
class VarList(object): # {{{
	def __init__(self, *args):
		if len(args) == 1 and isinstance(args[0], root.RooArgList):
			self.list = args[0]
		else:
			self.list = root.RooArgList(*[_change(x).var for x in args])
		VarList_cache.append(self)
	def __getattr__(self, name):
		return self.list.__getattribute__(name)
	def __len__(self):
		return self.getSize()
	def __getitem__(self, key):
		ret = self.at(key)
		if not ret:
			raise IndexError
		return ret
	__setitem__ = NotImplemented
# }}}

class VarSet(object): # {{{
	def __init__(self, *args):
		if len(args) == 1 and isinstance(args[0], root.RooArgSet):
			self.set = args[0]
		else:
			self.set = root.RooArgSet(*[_change(x).var for x in args])
	def __getattr__(self, name):
		return self.set.__getattribute__(name)
	def __len__(self):
		return self.getSize()
# }}}

class VarTuple(tuple): # {{{
	def __new__(cls, *args, **kwargs):
		return super(VarTuple, cls).__new__(cls, tuple(*args, **kwargs))
	def __lshift__(self, t):
		self.setVal(t)
		return self
	def __and__(self, t):
		if isinstance(t, bool):
			for var in self:
				var & t
		else:
			if len(self) != len(t):
				raise IndexError(t)
			for var, num in zip(self, t):
				var & num
		return self
	def getVal(self):
		return tuple(x.getVal() for x in self)
	def setVal(self, t):
		if len(self) != len(t):
			raise IndexError(t)
		for var, num in zip(self, t):
			var.var.setVal(num)
	@property
	def list(self):
		return VarList(*self)
	def ArgSet(self):
		return root.RooArgSet(*[x.var for x in self])
	def ArgList(self):
		return root.RooArgList(*[x.var for x in self])
# }}}

class VarFormula(Var): # {{{
	def __init__(self, title, l, name=None):
		if name is None:
			name = super(VarFormula, self)._gen_name()
		if isinstance(l, VarList):
			varlist = l.list
		elif isinstance(l, root.RooArgList):
			varlist = l
		elif isinstance(l, list):
			varlist = VarList(*l).list
		else:
			raise TypeError
		super(VarFormula, self).__init__(root.RooFormulaVar(name, title, varlist))
# }}}

class AllPdf(object): # {{{
	def __init__(self, pdf):
		self.pdf = pdf
# }}}

class ExtendedPdf: # {{{
	__slots__ = ('pair',)
	def __init__(self, t):
		self.pair = list(t)
	def __add__(self, other):
		return ExtendedPdf(self.pair + other.pair)
	def __iadd__(self, other):
		self.pair.extend(other.pair)
		return self
	def __getitem__(self, index):
		return self.pair[index]
# }}}

class Add(AutoNaming, AllPdf): # {{{
	def __init__(self, *args, **kwargs):
		if len(args) != 0 and isinstance(args[0], ExtendedPdf):
			if len(args) >= 2 and type(args[1]) == str:
				name = args[1]
			else:
				name = self._gen_name()
			var = [x[0].var for x in args[0].pair]
			pdfs = [x[1].pdf for x in args[0].pair]
			if 'Print' in Pdf.__dict__:
				Pdf.Print(name)
			if len(pdfs) < 10:
				super(Add, self).__init__(root.RooAddPdf(name, name, root.RooArgList(*pdfs), root.RooArgList(*var)))
			else:
				lp = root.RooArgList(*pdfs[:9])
				la = root.RooArgList(*var[:9])
				for i in range(9, len(pdfs)):
					lp.add(pdfs[i])
					la.add(var[i])
				super(Add, self).__init__(root.RooAddPdf(name, name, lp, la))
		else:
			raise TypeError(args)
	def __getattr__(self, name):
		return self.pdf.__getattribute__(name)
	def __getitem__(self, index):
		return AddPdfItem(self, index)
# }}}

class AddPdfItem(object): # {{{
	def __init__(self, add, index):
		self.pdf = add
		if isinstance(index, string_types):
			self.index = index
		elif isinstance(index, tuple):
			self.index = ','.join(index)
		else:
			raise TypeError
	def plotOn(self, frame, *args, **kwargs):
		return self.pdf.plotOn(frame, root.RooFit.Components(self.index), root.RooFit.Name(kwargs.get("name") or self.index), *args, **kwargs)
# }}}

class Pdf(AllPdf): # {{{
	_dct = {}
	def __init__(self, X, name, pdf):
		if isinstance(X, URooVarTypes):
			self.X = X
		elif isinstance(X, Var):
			self.X = X.var
		else:
			raise TypeError(X)
		if name in self._dct:
			raise ValueError('Pdf name repeated')
		if 'Print' in Pdf.__dict__:
			Pdf.Print(name)
		self._dct[name] = self
		super(Pdf, self).__init__(pdf)
	def __getattr__(self, name):
		return self.pdf.__getattribute__(name)
	@classmethod
	def get(cls, name):
		return cls._dct[name]
	def __mul__(self, other):
		if isinstance(other, Pdf):
			return Prod(self, other)
		raise NotImplemented
# }}}

def metapdf_withkw(typ_str, args_default): # {{{
	def _pdf(name, bases, dct):
		dct['typ_str'] = typ_str
		dct['args_default'] = args_default
		def __init__(self, X, *args, **kwargs):
			args = list(args)
			l = []
			for s in self.args_default:
				if len(args) != 0:
					l.append(_change(args.pop(0)))
				elif s in kwargs:
					l.append(_change(kwargs.pop(s)))
				elif s + '_init' in kwargs:
					l.append(_change(kwargs.pop(s + '_init'), True))
				else:
					l.append(Var())
			if len(args) >= 1 and isinstance(args[0], string_types):
				name = args.pop(0)
			elif 'name' in kwargs:
				name = kwargs.pop('name')
			else:
				name = self._gen_name()
			if len(args) != 0 or len(kwargs) != 0:
				raise TypeError
			for typ in bases:
				typ.__init__(self)
			Pdf.__init__(self, X, name, None)
			if isinstance(self.typ_str, str):
				self.pdf = root.__getattr__(self.typ_str)(name, name, self.X, *map(lambda x: x.var, l))
			else:
				print(l)
				self.pdf = self.typ_str(name, self.X, *map(lambda x: x.var, l))
		dct['__init__'] = __init__
		return type(name, bases + (AutoNaming, Pdf), dct)
	return _pdf
# }}}

@add_metaclass(metapdf_withkw('RooGaussian', ('mean', 'sigma')))
class Gaus:
	pass
@add_metaclass(metapdf_withkw('RooArgusBG', ('m0', 'c', 'p')))
class Argus:
	pass
@add_metaclass(metapdf_withkw('RooCBShape', ('mean', 'sigma', 'asym', 'amp')))
class Crys:
	pass
@add_metaclass(metapdf_withkw('RooBreitWigner', ('mean', 'sigma')))
class BW:
	pass

dblgaus_cache = []
def _build_dblgaus(self, name, X, varfrac, mean1, sigma1, mean2, sigma2):
	name1 = Gaus._gen_name()
	name2 = Gaus._gen_name()
	gaus1 = root.RooGaussian(name1, name1, X, mean1, sigma1)
	gaus2 = root.RooGaussian(name2, name2, X, mean2, sigma2)
	list1 = root.RooArgList(gaus1, gaus2)
	list2 = root.RooArgList(varfrac)
	dblgaus_cache.extend([gaus1, gaus2, list1, list2])
	return root.RooAddPdf(name, name, list1, list2)
@add_metaclass(metapdf_withkw(_build_dblgaus, ('frac', 'mean1', 'sigma1', 'mean2', 'sigma2')))
class DblGaus:
	pass

class Poly(AutoNaming, Pdf): # {{{
	def __init__(self, X, *args, **kwargs):
		args = list(args)
		if len(args) >= 1 and isinstance(args[0], integer_types):
			l = [Var() for s in range(args[0])]
			args.pop(0)
		else:
			l = [_change(s) for s in args]
			args = []
		if len(args) >= 1 and type(args[0]) == str:
			name = args.pop(0)
		elif 'name' in kwargs:
			name = kwargs.pop('name')
		else:
			name = self._gen_name()
		self.l = l
		super(Poly, self).__init__(X, name, None)
		self.pdf = root.RooChebychev(name, name, self.X, root.RooArgList(*map(lambda x: x.var, l)))
# }}}

class Hist(AutoNaming, Pdf): # {{{
	def __init__(self, X, hist, name=None, intOrder=None, shift=None):
		self.hist = hist
		if name is None:
			name = self._gen_name()
		assert(isinstance(hist, root.RooDataHist))
		super(Hist, self).__init__(X, name, None)
		if shift is None:
			if intOrder is None:
				self.pdf = root.RooHistPdf(name, name, root.RooArgSet(self.X), hist)
			else:
				self.pdf = root.RooHistPdf(name, name, root.RooArgSet(self.X), hist, intOrder)
		else:
			shift_var = VarFormula("@0-@1", root.RooArgList(X.var, shift.var))
			if intOrder is None:
				self.pdf = root.RooHistPdf(name, name, VarList(shift_var).list, VarList(X).list, hist)
			else:
				self.pdf = root.RooHistPdf(name, name, VarList(shift_var).list, VarList(X).list, hist, intOrder)
# }}}

class Keys(AutoNaming, Pdf): # {{{
	def __init__(self, X, dataset, name=None, keys_args=None):
		self.dataset = dataset
		if name is None:
			name = self._gen_name()
		assert(isinstance(dataset, root.RooDataSet))
		super(Keys, self).__init__(X, name, None)
		if keys_args is None:
			self.pdf = root.RooKeysPdf(name, name, self.X, dataset)
		else:
			self.pdf = root.RooKeysPdf(name, name, self.X, dataset, *keys_args)
# }}}

class Prod(AutoNaming, Pdf): # {{{
	def __init__(self, X, pdf1, pdf2, name=None):
		if name is None:
			name = self._gen_name()
		super(Prod, self).__init__(X, name, None)
		self.pdf = root.RooProdPdf(name, name, pdf1.pdf, pdf2.pdf)
# }}}

class Conv(AutoNaming, Pdf): # {{{
	def __init__(self, X, pdf1, pdf2, name=None):
		if name is None:
			name = self._gen_name()
		if isinstance(pdf1, AllPdf):
			pdf1 = pdf1.pdf
		if isinstance(pdf2, AllPdf):
			pdf2 = pdf2.pdf
		super(Conv, self).__init__(X, name, None)
		self.pdf = root.RooFFTConvPdf(name, name, self.X, pdf1, pdf2)
# }}}

class DoubleGausAdded(AutoNaming, ExtendedPdf):
	pass #TODO
		#sigd = Var(ROOT.RooFormulaVar(name, name, "{0} * {1}".format('nd', 'dpercent'), VarList(Var.nd, Var.dpercent).list)) \
		#		* Gaus(X, Var.massd(1.869, 1.864, 1.874), Var.sigmad(0.01, 0, 0.05)) +\
		#		Var(ROOT.RooFormulaVar(name2, name2, "{0} * (1 - {1})".format('nd', 'dpercent'), VarList(Var.nd, Var.dpercent).list)) \
		#		* Gaus(X, Var.massd, Var.sigmad2(0.02, 0, 0.05))

class Slice(AutoNaming):
	pass
class Simu(AutoNaming, Pdf): # {{{
	def __init__(self, X, *args, **kwargs):
		length = len(args)
		if 'name' in kwargs:
			self.name = kwargs.pop('name')
		else:
			self.name = self._gen_name()
		self.slice_names = AutoNaming._gen_names(length, self.name + '_')
		self.slice_name = Slice._gen_name()
		self.category = root.RooCategory(self.slice_name, self.slice_name)
		for name in self.slice_names:
			self.category.defineType(name)
		super(Simu, self).__init__(X, self.name, None)
		self.pdf = root.RooSimultaneous(self.name, self.name, self.category)
		for name, pdf in zip(self.slice_names, args):
			self.pdf.addPdf(pdf.pdf, name)
		if 'Print' in Pdf.__dict__:
			Pdf.Print((self.name, self.slice_name, self.slice_names))
		self.pdfs = args
	def consDataArgs(self, *args):
		if len(args) != len(self.pdfs):
			raise IndexError
		return (root.RooFit.Index(self.category),) + tuple(root.RooFit.Import(name, data) for name, data in zip(self.slice_names, args))
	def plotDataArgs(self, index):
		return (root.RooFit.Cut("%s==%s::%s" % (self.slice_name, self.slice_name, self.slice_names[index])),)
	def __getitem__(self, index):
		if isinstance(index, int):
			name = self.slice_names[index]
		else:
			name = index
		return SimuItem(self, name)
# }}}
class SimuItem(object): # {{{
	def __init__(self, simu, name):
		self.simu = simu
		self.name = name
	def plotOn(self, frame, *args, **kwargs):
		data = kwargs.get('data')
		if data is None:
			return self.simu.pdf.plotOn(frame, root.RooFit.Slice(self.simu.category, self.name), root.RooFit.Name(kwargs.get("name") or self.name), *args)
		else:
			return self.simu.pdf.plotOn(frame, root.RooFit.Slice(self.simu.category, self.name), root.RooFit.ProjWData(root.RooArgSet(self.simu.category), data), root.RooFit.Name(kwargs.get("name") or self.name), *args)
	def __getitem__(self, index):
		return SimuAddPdfItem(self, index)
# }}}
class SimuAddPdfItem(object): # {{{
	def __init__(self, simu, index):
		self.simu = simu
		if isinstance(index, string_types):
			self.index = index
		elif isinstance(index, tuple):
			self.index = ','.join(index)
		else:
			raise TypeError
	def plotOn(self, frame, *args, **kwargs):
		return self.simu.plotOn(frame, root.RooFit.Components(self.index), root.RooFit.Name(kwargs.get("name") or self.index), *args, **kwargs)
# }}}

_DataHist_temp = 0
datahist_cache = []
def DataHist(listvar, hist, name=None): # {{{
	global _DataHist_temp
	if isinstance(listvar, list):
		arglist = root.RooArgList(*[(X if isinstance(X, URooVarTypes) else X.var) for X in listvar])
	else:
		arglist = root.RooArgSet(*[(X if isinstance(X, URooVarTypes) else X.var) for X in listvar])
	if name is None:
		name = 'datahist_' + str(_DataHist_temp)
		_DataHist_temp += 1
	if 'Print' in Var.__dict__:
		Var.Print(name)
	ret = root.RooDataHist(name, name, arglist, hist)
	datahist_cache.append(ret)
	return ret
# }}}

_DataSet_temp = 0
dataset_cache = []
def DataSet(listvar, tree, name=None): # {{{
	global _DataSet_temp
	argset = root.RooArgSet(*[(X if isinstance(X, URooVarTypes) else X.var) for X in listvar])
	if name is None:
		name = 'dataset_' + str(_DataSet_temp)
		_DataSet_temp += 1
	if 'Print' in Var.__dict__:
		Var.Print(name)
	ret = root.RooDataSet(name, name, tree, argset)
	dataset_cache.append(ret)
	return ret
# }}}

# vim: fdm=marker
