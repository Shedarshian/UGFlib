#import ROOT as root
import contextlib
import sys
class _root:
	def __getattr__(self, name):
		return sys.modules['ROOT'].__getattr__(name)
root = _root()

class Arrow:
	def __init__(self, t1, t2, arrowsize=0.02, option="|>", color=None):
		self.t1 = t1
		self.t2 = t2
		self.arrowsize = arrowsize
		self.option = option
		self.color = root.RooFit.kRed if color is None else color
	def construct(self):
		ar = root.TArrow(self.t1[0], self.t1[1], self.t2[0], self.t2[1], self.arrowsize, self.option)
		ar.SetLineColor(self.color)
		ar.SetFillColor(self.color)
		return ar

# ROOT helper function
@contextlib.contextmanager
def open(path, name):
	f = root.TFile(path)
	yield f.Get(name)
def TH1F(name, *els, **kwargs):
	h1 = root.TH1F(name, name, *els)
	if "axename" in kwargs:
		FormatData(h1)
		NameAxes(h1, *kwargs['axename'])
	return h1
def Var(name, *els):
	return root.RooRealVar(name, name, *els)
def _construct_dblname(typ):
	def _(name, parents, attrs):
		if 'args' in attrs:
			return typ(name, name, *attrs['args'])
		else:
			return typ(name, name)
	return _
def _construct(typ):
	def _(name, parents, attrs):
		if 'args' in attrs:
			return typ(name, *attrs['args'])
		else:
			return typ(name)
	return _
#var = _construct_dblname(root.RooRealVar)

def DrawLatex(pos, text, size = 0.10):
	l = root.TLatex()
	l.SetTextSize(size)
	l.SetNDC(True)
	l.DrawLatex(pos[0], pos[1], text)

# y axename helper
def Yname(Range, no2=False, add_space=False, c=False):
	#Range: (Nbin, L, R)
	slash = " / " if add_space else '/'
	cs = "#it{c}" if c else 'c'
	if no2:
		return "Events%s%.1f (MeV/%s)" % (slash, (Range[2] - Range[1]) * 1.0 / Range[0] * 1000, cs)
	return "Events%s%.1f (MeV/%s^{2})" % (slash, (Range[2] - Range[1]) * 1.0 / Range[0] * 1000, cs)

_RealEnergy = {4470: "4.467 GeV", 4530: "4.527 GeV", 4575: "4.575 GeV", 4600: "4.600 GeV", 4540: "4.540 GeV", 4550: "4.550 GeV", 4560: "4.560 GeV", 4570: "4.570 GeV", 4580: "4.580 GeV", 4590: "4.590 GeV", 4612: "4.612 GeV", 4626: "4.626 GeV", 4640: "4.640 GeV", 4660: "4.660 GeV", 4680: "4.680 GeV", 4700: "4.700 GeV", 4740: "4.740 GeV", 4750: "4.750 GeV", 4780: "4.780 GeV", 4840: "4.843 GeV", 4914: "4.918 GeV", 4946: "4.951 GeV"}
def realEnergy(Em):
	return _RealEnergy[Em]
def realEnergyNum(Em):
	return {4470: 4.467, 4530: 4.527, 4575: 4.575, 4600: 4.600, 4540: 4.540, 4550: 4.550, 4560: 4.560, 4570: 4.570, 4580: 4.580, 4590: 4.590, 4612: 4.612, 4626: 4.626, 4640: 4.640, 4660: 4.660, 4680: 4.680, 4700: 4.700, 4740: 4.740, 4750: 4.750, 4780: 4.780, 4840: 4.843, 4914: 4.918, 4946: 4.951}[Em]

def DrawEnergy(pos, Em, size = 0.10):
	DrawLatex(pos, "#sqrt{s} = " + realEnergy(Em), size=size)


# draw options
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

def SetStyle():
	#from ROOT import gStyle
	gStyle = root.gStyle
	gStyle.SetErrorX(0);
	
	gStyle.SetOptTitle(0);
	gStyle.SetOptStat(0);
	gStyle.SetOptFit(0);
	
	gStyle.SetLabelFont(42,"xyz");
	gStyle.SetLabelSize(0.06,"xyz");
	gStyle.SetLabelOffset(0.01,"xyz");
	
	gStyle.SetTitleFont(42,"xyz");
	gStyle.SetTitleColor(1,"xyz");
	gStyle.SetTitleSize(0.07,"xyz");
	gStyle.SetTitleOffset(0.9,"yz");
	gStyle.SetTitleOffset(1.1,"x");
	
	gStyle.SetPadBorderMode(0);
	gStyle.SetPadBorderSize(0);
	
	gStyle.SetPadLeftMargin(0.14);
	gStyle.SetPadBottomMargin(0.17);
	gStyle.SetPadRightMargin(0.03);
	gStyle.SetPadTopMargin(0.01);
	
	gStyle.SetPadTickX(1);
	gStyle.SetPadTickY(1);

def SetPad(i = None):
	gPad = root.gPad
	gPad.SetTopMargin(0.01);
	gPad.SetBottomMargin(0.17);
	gPad.SetLeftMargin(0.14);
	if i is not None:
		gPad.SetRightMargin(0.03);

