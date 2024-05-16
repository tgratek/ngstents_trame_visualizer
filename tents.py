import ngsolve as ng
from ngstents import TentSlab
from netgen.geom2d import EdgeInfo as EI, Solid2d, CSG2d
from ngsolve.webgui import Draw
from ngsolve import L2, GridFunction, x, y, exp, CF

geo = CSG2d()
horn = Solid2d(
    [(1, 0.55),
     EI((1, 1), bc='out'),      # right curved boundary (with control point)
     (0, 1),
     EI((-1,  1), bc='out'),    # left curved bdry
     (-1, 0.55),
     EI(bc='cone'),             # conical walls
     (-0.03, 0),
     EI(maxh=0.02, bc='pipe'),  # feed pipe
     (-0.03, -0.5),
     EI(maxh=0.02, bc='in'),
     (+0.03, -0.5),
     EI(maxh=0.02, bc='pipe'),
     (+0.03, 0),
     EI(bc='cone')
     ], mat='air')
geo.Add(horn)
mesh = ng.Mesh(geo.GenerateMesh(maxh=0.15))
mesh.Curve(4)

s = y+0.2; d = 500               # initial wave
phi = exp(-s**2 * d); dphi = 2 * d * s * phi
q0 = CF((0, -dphi)); mu0 = -dphi; u0 = CF((q0, mu0))
# scene = Draw(u0, mesh)
ts = TentSlab(mesh)
wavespeed = 1
dt = 0.05
ts.SetMaxWavespeed(wavespeed)
ts.PitchTents(dt=dt, local_ct=True, global_ct=1/2)
ts.MaxSlope()
msh, v, w = ts.DrawPitchedTents(uptolevel=1)
ts.DrawPitchedTentsVTK('tents')