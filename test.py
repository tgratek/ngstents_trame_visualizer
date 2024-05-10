# All code from provided jupyter notebook
# Try netgen .\test.py -> brings up netgen gui with last(?) tent

import ngsolve as ng
from ngstents import TentSlab
from ngsolve.meshes import Make1DMesh
from netgen.geom2d import EdgeInfo as EI, Solid2d, CSG2d
from ngsolve.webgui import Draw
from ngsolve import L2, GridFunction, x, y, exp, CF
from ngstents.conslaw import Wave

# 2
mesh = Make1DMesh(4) 
ts = TentSlab(mesh)
# ts.DrawPitchedTentsPlt() # Commented out - brings up python matplot

# 3
dt = 0.3 

# 4
c = 3
ts.SetMaxWavespeed(c)

#5
ts.PitchTents(dt) 

#6
# ts.DrawPitchedTentsPlt(showtentnums=True)  # Commented out - brings up python matplot

#7
print('Number of tents: ', ts.GetNTents()) 
print('Maximal tent slope: ', ts.MaxSlope())

#8
n = 6 
t = ts.GetTent(n)
print('Details of Tent #%d:' % n)
print('  Pitching (central) vertex number:', t.vertex)
print('  Neighbor vertex numbers:', list(t.nbv))
print('  Tent element numbers:',    list(t.els))
print('  Neighbor vertex heights:', list(t.nbtime))
mesh = Make1DMesh(7, mapping=lambda x: 1-x**2) #9
for v in mesh.vertices: print(v.point)

#10
ts = TentSlab(mesh) 
ts.SetMaxWavespeed(c)
ts.PitchTents(dt)
# ts.DrawPitchedTentsPlt() # Commented out - brings up python matplot

#11
mesh = Make1DMesh(35) 
dt = 0.2
ts = TentSlab(mesh)
ts.SetMaxWavespeed(1 + ng.CF(ng.exp(-100 * (ng.x-0.5)**2)))
ts.PitchTents(dt)
# ts.DrawPitchedTentsPlt() # Commented out - brings up python matplot

#12
geo = CSG2d() 
horn = Solid2d(
    [(1, 0.55), EI((1, 1), bc='out'),       # right curved boundary (with control point)
     (0, 1), EI((-1, 1), bc='out'),         # left curved bdry
     (-1, 0.55), EI(bc='cone'),             # conical walls
     (-0.03, 0), EI(maxh=0.02, bc='pipe'),  # feed pipe
     (-0.03, -0.5), EI(maxh=0.02, bc='in'),
     (+0.03, -0.5), EI(maxh=0.02, bc='pipe'),
     (+0.03, 0), EI(bc='cone')
     ],
    mat='air')
geo.Add(horn)
mesh = ng.Mesh(geo.GenerateMesh(maxh=0.5))
mesh.Curve(4)
s = y+0.2
d = 500                                      # initial wave
phi = exp(-s**2 * d)
dphi = 2 * d * s * phi
q0 = CF((0, -dphi))
mu0 = -dphi; u0 = CF((q0, mu0))
scene = Draw(u0, mesh)

# 13
ts = TentSlab(mesh) 
wavespeed = 1
dt = 0.05
ts.SetMaxWavespeed(wavespeed)
ts.PitchTents(dt=dt, local_ct=True, global_ct=1/2)
ts.MaxSlope()

# 14
msh, v, w = ts.DrawPitchedTents(uptolevel=1) # Bad performance when levels increased (from sponsors note)
Draw(msh)

# 15
# ts.DrawPitchedTentsVTK(file.vtk) # Original from notebook, doesn't work (file is a keyword)
ts.DrawPitchedTentsVTK('file')     # Creates a VTK file: "file.vtk" in directory

# 16
V = L2(mesh, order=2, dim=mesh.dim+1)
u = GridFunction(V, "u")
wave = Wave(u, ts, inflow=mesh.Boundaries('in'),
            transparent=mesh.Boundaries('out'),
            reflect=mesh.Boundaries('pipe|cone'))

# 17
wave.SetTentSolver(substeps=15)

# 18
ut = ng.GridFunction(V, multidim=0)
ut.AddMultiDimComponent(u.vec)

# 19
wave.SetInitial(u0)
scene = Draw(u)
t = 0
with ng.TaskManager():
    while t < 0.7:
        wave.Propagate()   # Solve in the current spacetime slab
        t += dt

        # If the solution went by too fast, uncomment this:
        # input(' Time {:.3f}.'.format(t) + ' Compute next time slab?')
        ut.AddMultiDimComponent(u.vec)   # Store the solution at current slab top
        
        # scene.Redraw() # ** Commented out - Errors python - Redraw() error on object

# 20        
Draw(ut, mesh, autoscale=False, min=1, max=5, interpolate_multidim=True, animate=True)
