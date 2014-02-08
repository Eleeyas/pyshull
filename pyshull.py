
def CalcDist(a, b):
	#Pythagorean theorem
	return ((a[0] - b[0]) ** 2. + (a[1] - b[1]) ** 2.) ** 0.5

def RadialDistance(pts, seedIndex):
	dists = []
	seedPt = pts[seedIndex]

	for ptNum, pt in enumerate(pts):
		dist = CalcDist(pt, seedPt)
		dists.append((dist, ptNum))

	dists.sort()
	return dists

def FindSmallestCircumCircle(pts, firstIndex, secondIndex):

	#http://www.mathopenref.com/trianglecircumcircle.html
	a = CalcDist(pts[firstIndex], pts[secondIndex])
	
	diams = []
	for ptNum, pt in enumerate(pts):
		if ptNum == firstIndex:
			continue
		if ptNum == secondIndex:
			continue
		b = CalcDist(pts[firstIndex], pts[ptNum])
		c = CalcDist(pts[secondIndex], pts[ptNum])

		#https://en.wikipedia.org/wiki/Heron%27s_formula#Numerical_stability
		x1 = (a+(b+c))
		x2 = (c-(a-b))
		x3 = (c+(a-b))
		x4 = (a+(b-c))
		x = x1*x2*x3*x4
		if x > 0.:
			sqrtx = x**0.5
			if sqrtx > 0.:
				diam = 0.5*a*b*c/sqrtx
				diams.append((diam, ptNum))
				#print ptNum, a, b, c
			else:
				#Prevent division by zero
				diams.append((float("inf"), ptNum))
		else:
			#Numerical instability detected
			diams.append((float("inf"), ptNum))
	
	diams.sort()
	return diams

def CircumCircleCentre(pta, ptb, ptc):
	#https://en.wikipedia.org/wiki/Circumscribed_circle#Cartesian_coordinates
	pta2 = (pta[0]**2.+pta[1]**2.)
	ptb2 = (ptb[0]**2.+ptb[1]**2.)
	ptc2 = (ptc[0]**2.+ptc[1]**2.)

	d = 2.*(pta[0]*(ptb[1]-ptc[1])+ptb[0]*(ptc[1]-pta[1])+ptc[0]*(pta[1]-ptb[1]))

	ux = (pta2*(ptb[1]-ptc[1]) + ptb2*(ptc[1]-pta[1]) + ptc2*(pta[1]-ptb[1])) / d
	uy = (pta2*(ptc[0]-ptb[0]) + ptb2*(pta[0]-ptc[0]) + ptc2*(ptb[0]-pta[0])) / d

	return ux, uy

def RightHandedCheck(pts, pt1, pt2, pt3):
	vec21 = (pts[pt1][0] - pts[pt2][0], pts[pt1][1] - pts[pt2][1])
	vec23 = (pts[pt3][0] - pts[pt2][0], pts[pt3][1] - pts[pt2][1])
	return vec21[0] * vec23[1] - vec21[1] * vec23[0]

def FormTriangles(pts, seedTriangle, orderToAddPts):
	#print pts
	#print seedTriangle
	#print orderToAddPts
	
	triangles = [seedTriangle]
	hull = seedTriangle[:]

	for ptToAdd in orderToAddPts:
		#print "adding point", ptToAdd, pts[ptToAdd]

		#Check which hull faces are visible
		visInd = []
		for hInd in range(len(hull)):
			#print pts[hull[hInd]], pts[hull[(hInd+1) % len(hull)]]
			vis = RightHandedCheck(pts, hull[hInd], hull[(hInd+1) % len(hull)], ptToAdd)
			#print "vis", hInd, vis
			if vis <= 0.:
				visInd.append(hInd)

		if len(visInd) == 0:
			raise Exception("No hull sides visible")

		#Check for range of sides that are visible
		firstSide = 0
		while firstSide in visInd:
			firstSide += 1
			if firstSide >= len(hull):
				raise Exception("No sides are not visible to point")

		while firstSide not in visInd:
			firstSide = (firstSide + 1) % len(hull)
		
		lastSide = firstSide
		while (lastSide+1) % len(hull) in visInd:
			lastSide = (lastSide+1) % len(hull)

		#Get copy of retained section of hull
		cursor = (lastSide + 1) % len(hull)
		newHull = []
		iterating = True
		while iterating:
			newHull.append(hull[cursor])
			if cursor in visInd:
				iterating = False
			cursor = (cursor + 1) % len(hull)

		#Add new point to hull
		newHull.append(ptToAdd)

		#Form new triangles
		cursor = firstSide
		iterating = True
		while iterating:
			tri = (hull[cursor], ptToAdd, hull[(cursor+1)%len(hull)])
			#print "Found triangle", tri
			triangles.append(tri)

			if cursor == lastSide:
				iterating = False
			cursor = (cursor + 1) % len(hull)

		#print "newhull" , newHull
		hull = newHull
	return hull, triangles

def PySHull(pts):
	#S-hull: a fast sweep-hull routine for Delaunay triangulation by David Sinclair
	#http://www.s-hull.org/
	
	#Select seed point
	seedIndex = 0

	#Sort by radial distance
	radialSorted = RadialDistance(pts, seedIndex)

	#Nearest point to seed point
	nearestToSeed = radialSorted[1][1]

	#Find third point that creates the smallest circum-circle
	sortedCircumCircles = FindSmallestCircumCircle(pts, seedIndex, nearestToSeed)
	thirdPtIndex = sortedCircumCircles[0][1]

	#Order points to be right handed
	crossProd = RightHandedCheck(pts, seedIndex, nearestToSeed, thirdPtIndex)
	if crossProd < 0.:
		#Swap points
		secondPtInd = thirdPtIndex
		thirdPtIndex = nearestToSeed
	else:
		#Already right handed
		secondPtInd = nearestToSeed

	#Centre of circum-circle
	centre = CircumCircleCentre(pts[seedIndex], pts[secondPtInd], pts[thirdPtIndex])

	#Sort points by distance from circum-circle centre
	dists = []
	for ptNum, pt in enumerate(pts):
		if ptNum == seedIndex: continue
		if ptNum == secondPtInd: continue
		if ptNum == thirdPtIndex: continue
		
		dist = CalcDist(pts[ptNum], centre)
		dists.append((dist, ptNum))
	dists.sort()
	orderToAddPts = [v[1] for v in dists]

	#Form triangles by sequentially adding points
	hull, triangles = FormTriangles(pts, (seedIndex, secondPtInd, thirdPtIndex), orderToAddPts)

	#Flip adjacent pairs of triangles to meet Delaunay condition
	#https://en.wikipedia.org/wiki/Delaunay_triangulation#Visual_Delaunay_definition:_Flipping
	#TODO
	
	return triangles

