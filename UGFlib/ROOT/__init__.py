import ROOT as root
import hashlib
import rootpy

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


