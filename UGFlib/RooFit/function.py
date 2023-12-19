class Crystal_ball:
	def __call__(self, x, param):
		AA, a, sigma, n, x0 = param
		x = x[0]
		if sigma < 0 or n < 0:
			return 0
		x = (x - x0) / sigma
		if a < 0:
			x = -x
		a_abs = abs(a)
		if x > -a_abs:
			return AA * math.exp(-x ** 2 / 2)
		else:
			A = pow(n / a_abs, n) * math.exp(-a_abs ** 2 / 2)
			B = n / a_abs - a_abs
			return AA * A * pow(B - x, -n)
