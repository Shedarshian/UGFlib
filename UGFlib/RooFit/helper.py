import ROOT as root
import more_itertools
from typing import Callable
from abc import ABCMeta, abstractmethod
import decimal
from collections import namedtuple
import math, re
from numbers import Number

def FormatData(datahist):
	datahist.SetMarkerStyle(20)
	datahist.SetMarkerSize(1)
	datahist.SetLineWidth(2)
	if isinstance(datahist, root.TH1):
		FormatAxisX(datahist.GetXaxis())
		FormatAxisY(datahist.GetYaxis())
def FormatAxisX(axis):
	axis.SetLabelFont(42)
	axis.SetLabelSize(0.06)
	axis.SetLabelOffset(0.01)
	axis.SetNdivisions(510)
	axis.SetTitleFont(42)
	axis.SetTitleColor(1)
	axis.SetTitleSize(0.07)
	axis.SetTitleOffset(1.)
def FormatAxisY(axis):
	axis.SetLabelFont(42)
	axis.SetLabelSize(0.06)
	axis.SetLabelOffset(0.01)
	axis.SetNdivisions(510)
	axis.SetTitleFont(42)
	axis.SetTitleColor(1)
	axis.SetTitleSize(0.07)
	axis.SetTitleOffset(1.)
def NameAxes(datahist, xname, yname):
	datahist.GetXaxis().SetTitle(xname)
	datahist.GetYaxis().SetTitle(yname)

class _color:
	def __call__(self, attr):
		return self.__getattr__(attr)
	def __getattr__(self, attr):
		match = re.match('^([^_\d]*)(_?)(\d+)$', attr)
		n = 0
		if match:
			n = (-1 if match.group(2) != "" else 1) * int(match.group(3))
			attr = match.group(1)
		if attr == 'bkg':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kRed + n))
		elif attr == 'cyan':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kCyan + n))
		elif attr == 'violet':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kViolet + n))
		elif attr == 'orange':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kOrange + n))
		elif attr == 'yellow':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kYellow + n))
		elif attr == 'bluedot':
			return (root.RooFit.LineStyle(root.kDotted), root.RooFit.LineColor(root.kBlue + n))
		elif attr == 'blue':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kBlue + n))
		elif attr == 'green':
			return (root.RooFit.LineStyle(root.kDotted), root.RooFit.LineColor(root.kGreen + n))
		elif attr == 'magenta':
			return (root.RooFit.LineStyle(root.kDashed), root.RooFit.LineColor(root.kMagenta + n))
		elif attr == 'red':
			return (root.RooFit.LineColor(root.kRed + n),)
		elif attr == 'brown':
			return (root.RooFit.LineStyle(9), root.RooFit.LineColor(28))
	class _stack:
		def __call__(self, attr, offset=0):
			return (root.RooFit.DrawOption('F'), root.RooFit.FillColor(root.__getattr__('k' + attr) + offset), root.RooFit.VLines(), root.RooFit.LineWidth(0))
		def __getattr__(self, attr):
			return self(attr)
	Stack = _stack()
Color = _color()

def RedArrow():
	ar = root.TArrow()
	ar.SetLineColor(2)
	ar.SetFillColor(2)
	return ar
def RedLine():
	ar = root.TLine()
	ar.SetLineColor(2)
	return ar

def FitArgs(i):
	if i == 0:
		return (root.RooFit.Save(), root.RooFit.Extended(True), root.RooFit.Minos(True))

def significance(model, data, N_var, nll=None, args=None, Print=None, draw=None):
	if args is None:
		args = FitArgs(0)
	tmp = N_var.getVal()
	N_var.setVal(0)
	N_var.setConstant(True)
	nll0 = model.fitTo(data, *args).minNll()
	if draw is not None:
		c = draw()
		#from getpass import getpass
		#getpass('signi Enter...')
	N_var.setVal(tmp)
	N_var.setConstant(False)
	if nll is None:
		nll = model.fitTo(data, *args).minNll()
	if Print is not None:
		Print(('N_var, nll, nll0: ', float(N_var), nll, nll0))
	if nll0 < nll:
		if Print is not None:
			Print('Sni wrong!')
		return -(2 * (nll - nll0)) ** 0.5
	return (2 * (nll0 - nll)) ** 0.5

def drange(start, stop, step=1):
	while start < stop:
		yield start
		start += step
def decimal_range(start, stop, step='1'):
	return drange(decimal.Decimal(start), decimal.Decimal(stop), decimal.Decimal(step))

class _Likelihood(object):
	item = namedtuple('item', 'n, val, nll')
	cache = []
	def __init__(self):
		self.data = []
	def __setitem__(self, index, item):
		it = _Likelihood.item(index, *item)
		for i, (n, val, nll) in enumerate(self.data):
			if n == index:
				self.data[i] = it
				return
		self.data.append(it)
	def __getitem__(self, index):
		for n, val, nll in self.data:
			if n == index:
				return val, nll
		raise IndexError
	def __iter__(self):
		return iter(self.data)
	def upper_limit(self, CL=0.9):
		s = 0
		for n, val, nll in self:
			s += val
		p = 0
		for x in self:
			p += x.val
			if p >= CL * s:
				return x
	def __str__(self):
		return '\n'.join(['{0} {1}'.format(n, val) for n, val, nll in self.data])
	def conv(self, err, trunc=7):
		l2 = _Likelihood()
		step = float(self.data[1][0] - self.data[0][0])
		for x, y, nll in self:
			l2[x] = 0., 0.
			for x2, y2, nll in self:
				if x2 != 0 and x != 0:
					l2[x] = l2[x][0] + y2 * math.exp(-float(x2 - x) ** 2 / (2 * (err * float(x2)) ** 2)) / (math.sqrt(2 * math.pi) * err * float(x2)) * step, 0.
		d = (l2.data[trunc + 1][1] - l2.data[trunc][1]) * 1.0 / step
		for i in range(trunc):
			l2[l2.data[i][0]] = l2.data[trunc][1] - (trunc - i) * d, 0.
		return l2
	def save(self, f):
		for n, val, nll in self.data:
			f.writeline('{0} {1}'.format(n, val))
	def enlong(self, end):
		step = self.data[1][0] - self.data[0][0]
		for i in drange(self.data[-1][0] + step, end, step):
			self[i] = (0, 0)
	@staticmethod
	def load_str(f):
		import re
		l = _Likelihood()
		for line in f.split('\n'):
			match = re.match(r'(\d+(?:\.\d+)?) (\d+(?:\.\d+)?(?:e-?\d+)?)', line.strip())
			if not match:
				raise ValueError(line)
			n, val = match.group(1), match.group(2)
			l[decimal.Decimal(n)] = float(val), 0.
		return l
	@staticmethod
	def load(f):
		import re
		l = _Likelihood()
		for line in f:
			match = re.match(r'(\d+(?:\.\d+)?) (\d+(?:\.\d+)?(?:e-?\d+)?)', line)
			if not match:
				raise ValueError(line)
			n, val = match.group(1), match.group(2)
			l[decimal.Decimal(n)] = float(val), 0.
		return l
	def plot(self, E=None, U=False, if_pause=False):
		# E = ((0.3, 0.8), 4600, [0.10]) or E = 4600
		# U = 0.9 or U = True
		g = root.TGraph(len(self.data))
		for i, (n, val, nll) in enumerate(self.data):
			g.SetPoint(i, n, val)
		g.SetTitle('')
		g.GetXaxis().SetTitle('N_{sig}')
		g.GetXaxis().SetLabelSize(0.04)
		g.GetYaxis().SetTitle('likelihood')
		g.Draw('AC')
		if E is not None:
			from UGF.ROOT import DrawEnergy
			if isinstance(E, int):
				DrawEnergy((0.3, 0.8), E)
			else:
				DrawEnergy(*E)
		if U:
			if U == True:
				n, val, nll = self.upper_limit()
			else:
				n, val, nll = self.upper_limit(U)
			l = RedArrow()
			#l.SetLineWidth(0.02)
			if val * 1.6 > 0.8:
				#RedLine().DrawLine(float(n), g.GetYaxis().GetXmax(), float(n), g.GetYaxis().GetXmin())
				l.DrawArrow(float(n), val * 2.5, float(n), val * 1.6, 0.02, "|>")
			else:
				l.DrawArrow(float(n), max(val * 2.5, 1.0), float(n), val * 1.6, 0.02, "|>")
		if if_pause:
			from getpass import getpass
			getpass('Enter...')
		_Likelihood.cache.append(g)
		if U == True:
			return n

def likelihood(model, data, N_var, step=decimal.Decimal('0.1'), max=40, prnt=None, init=None, interpolation=None, args=None, ignore=(), extra_plot=None, must_init=False):
	if args is None:
		args = FitArgs(0)
	if isinstance(interpolation, Number):
		from copy import copy
		interpolation = ((copy(interpolation),),)
	tmp = N_var.getVal()
	N_var.setConstant(True)
	l = _Likelihood()
	nll0 = None
	for i in drange(0, max, step):
		if must_init and init:
			init()
		if i in ignore:
			l[i] = 0, 0
			if prnt:
				prnt((i, nll))
			continue
		N_var.setVal(i)
		nll = model.fitTo(data, *args).minNll()
		if i == 0:
			nll0 = nll
		if prnt:
			prnt((i, nll))
		try:
			l[i] = math.exp(nll0 - nll), nll
		except OverflowError:
			l[i] = 0, 0
			if init:
				init()
				nll = model.fitTo(data, *args).minNll()
				if prnt:
					prnt((i, nll))
				try:
					l[i] = math.exp(nll0 - nll), nll
				except OverflowError:
					l[i] = 0, 0
		if extra_plot is not None:
			extra_plot(i)
	N_var.setConstant(False)
	N_var.setVal(tmp)
	if not interpolation:
		interpolation = []
	else:
		interpolation = list(interpolation)
	for i, ((n1, val1, nll1), (n2, val2, nll2), (n3, val3, nll3)) in enumerate(more_itertools.windowed(l, 3)):
		if (nll1 < nll2 and nll2 > nll3 or nll1 > nll2 and nll2 < nll3) and i >= 1 and abs(nll2 - nll1) > 2 * abs(l.data[i - 1].nll - nll1):
			interpolation.append((n2,))
	if interpolation:
		for chunk in interpolation:
			ln = len(chunk)
			begin, nll0 = l[chunk[0] - step]
			end, nll1 = l[chunk[-1] + step]
			p = (end - begin) / (ln + 1)
			nllp = (nll1 - nll0) / (ln + 1)
			for index, val in zip(chunk, range(ln)):
				l[index] = begin + p * (val + 1), nll0 + p * (val + 1)
				if prnt:
					prnt((index, l[index]))
	return l

class FOM:
	__metaclass__ = ABCMeta
	def __init__(self, cutRange):
		self.val = []
		self.cutRange = cutRange
	@abstractmethod
	def read_excMC(self, *args, **kwargs):
		pass
	@abstractmethod
	def read_incMC(self, *args, **kwargs):
		pass
	@abstractmethod
	def apply_cut(self, dataset, cut, *args, **kwargs):
		pass
	@abstractmethod
	def signal(self, excMC, *args, **kwargs):
		return 0
	@abstractmethod
	def background(self, incMC, *args, **kwargs):
		return 1
	def save_individual_plot(self, dataset, path, if_exc, *args, **kwargs):
		pass
	def save(self, json_name):
		import json
		with open(json_name or 'FOM.json', 'w') as f:
			f.write(json.dumps([(float(i), val) for i, val in self.val]))
	def plot(self, path=None, title=('', ''), if_pause=True, draw_line=True, line_x=None):
		path = path or 'pic/FOM.eps'
		c = root.TCanvas()
		g = root.TGraph(len(self.val))
		for i, t in enumerate(self.val):
			g.SetPoint(i, float(t[0]), t[1])
		g.SetTitle('')
		g.GetXaxis().SetTitle(title[0])
		g.GetYaxis().SetTitle(title[1])
		g.SetMarkerColor(4)
		g.SetMarkerStyle(21)
		g.Draw("ALP")
		i, val = self.max
		if draw_line:
			line_x = line_x or float(i)
			RedLine().DrawLine(line_x, g.GetYaxis().GetXmax(), line_x, g.GetYaxis().GetXmin())
		#RedArrow().DrawArrow(float(i), max(val * 0.5, 1.0), float(i), val * 0.8, 0.02, "|>")
		c.SaveAs(path)
		if if_pause:
			from getpass import getpass
			getpass('pause...')
	def process(self, json_path=None, subplot_path=None):
		excMC = self.read_excMC()
		incMC = self.read_incMC()
		subplot_path = subplot_path or 'FOMsub_{0}_{1}.eps'
		for cut in self.cutRange:
			exc_cut = self.apply_cut(excMC, cut)
			s = self.signal(exc_cut)
			self.save_individual_plot(exc_cut, subplot_path.format(cut, 'exc'), True)
			inc_cut = self.apply_cut(incMC, cut)
			b = self.background(inc_cut)
			self.save_individual_plot(inc_cut, subplot_path.format(cut, 'inc'), False)
			self.val.append((cut, s / (s + b) ** 0.5))
		self.max = i, val = max(self.val, key=lambda x: x[1])
		if json_path is not None:
			self.save(json_path)

#class FOM_Dataset(FOM):
#	def __init__(self, cutRange, var, cut_var):
#		super(FOM_Dataset, self).__init__(cutRange)
#		self.var = var
#		self.cut_var = cut_var
#	def apply_cut(self, dataset, cut, *args, **kwargs):
#		return root.RooDataSet("temp_set", "temp_set", dataset, self.var, root.RooFormulaVar("cut", "cut", self.obtain_cut_formula(cut), root.RooArgList(self.var, self.cut_var)))
#	def obtain_cut_formula(self, cut):
#		return "{0} < {1}".format(self.cut_var.GetName(), cut)
#	def signal(self, excMC, *args, **kwargs):
#		return 0
#	def background(self, incMC, *args, **kwargs):
#		return 1
#	def save_individual_plot(self, dataset, path, *args, **kwargs):
#		pass

def getPull(h1, extended_pdf, nevent, X, rng, hname="pull", Print=None):
	h2 = extended_pdf.createHistogram(hname + "0", X.var, root.RooFit.Binning(rng[0]), root.RooFit.Extended(True))
	h2.Scale(nevent)
	hpull = root.TH1F(hname, hname, *rng)
	hpull.SetDirectory(0)
	for i in range(1, rng[0] + 1):
		n0 = h1.GetBinContent(i)
		nfit = h2.GetBinContent(i)
		if n0 > 0:
			pull = (nfit - n0) * 1.0 / n0 ** 0.5
			epull = (nfit * 1.0 / n0 + (1.0 + nfit * nfit) * 0.25 / n0 / n0) ** 0.5
		elif nfit > 0:
			pull = (nfit - n0) * 1.0 / nfit ** 0.5
			epull = (0.25 + n0 * 1.0 / nfit + n0 * n0 * 0.25 / nfit / nfit) ** 0.5
		else:
			pull = epull = 0.0
		if Print is not None:
			Print((pull, epull))
		hpull.SetBinContent(i, pull)
		hpull.SetBinError(i, epull)
	
	FormatData(hpull)
	hpull.GetYaxis().SetTitle("Pull")
	hpull.GetYaxis().SetTitleSize(0.1)
	#hpull.GetYaxis().SetLabelSize(0.15)
	hpull.GetYaxis().SetTitleOffset(0.3)
	hpull.GetXaxis().SetTitle("")
	return hpull

def drawPullLine(xmin, xmax):
	line = root.TLine(xmin, 0.0, xmax, 0.0)
	line.Draw()
	line.SetLineColor(2)
	line.SetLineStyle(2)
	line.SetLineWidth(2)
	line.DrawLine(xmin, -3.0, xmax, -3.0)
	line.DrawLine(xmin, 3.0, xmax, 3.0)

def getResidue(h1, extended_pdf, nevent, X, rng, hname="residue", Print=None, if_div=False):
	h2 = extended_pdf.createHistogram(hname + "0", X.var, root.RooFit.Binning(rng[0]), root.RooFit.Extended(True))
	h2.Scale(nevent)
	hpull = root.TH1F(hname, hname, *rng)
	hpull.Sumw2(True)
	hpull.SetDirectory(0)
	if if_div:
		hpull.Divide(h1, h2, 1, 1)
	else:
		hpull.Add(h1, h2, 1, -1)

	FormatData(hpull)
	hpull.GetYaxis().SetTitle("Residue")
	hpull.GetYaxis().SetTitleSize(0.1)
	#hpull.GetYaxis().SetLabelSize(0.15)
	hpull.GetYaxis().SetTitleOffset(0.3)
	hpull.GetXaxis().SetTitle("")
	return hpull

