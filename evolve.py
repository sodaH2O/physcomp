import numpy as np
from scipy import ndimage
#
#def heatDiffusionFunc(laplacian):
        #alpha = 0.00145 # diffusivity
        #return alpha*laplacian; 
def laplacianFunc(grid, dx, dy, topY):
        laplacian = np.zeros_like(grid) # stores lapacian value
        #for i in range(steps):
        # calculate laplacian of temperature at non-edge cell
        # with finite difference
        for i in range(1, len(grid)-1):
                for j in range(1, topY):
                        laplacian[i][j] = (grid[i-1][j]+grid[i+1][j]-2*grid[i][j])/(dx*dx)
                        laplacian[i][j] += (grid[i][j-1]+grid[i][j+1]-2*grid[i][j])/(dy*dy)

        return laplacian

def laplacianFuncVec(grid, dx, dy, topY):
        d2x = np.eye(grid.shape[1])
        d2x_roll1 = np.roll(d2x, 1, axis=0)
        d2x_roll2 = np.roll(d2x, -1, axis=0)
        d2x = d2x_roll1+d2x_roll2-2*d2x
        
        laplacian = np.dot(grid, d2x)/(dx*dx)

        d2y = np.eye(grid.shape[0])
        d2y_roll1 = np.roll(d2y, 1, axis=0)
        d2y_roll2 = np.roll(d2y, -1, axis=0)
        d2y = d2y_roll1+d2y_roll2-2*d2y
        
        laplacian += np.dot(d2y, grid)/(dy*dy)

        return laplacian

def f1(temp): #temp in Kelvin
        t = temp-273
        return -3.11e-4*t*t+3.48e-2*t + 0.0265

def f2(temp):
        t = temp-273
        return 2.142e-4*t*t-2.356e-2*t+1.348

def timeEvolve(pile, dt, ambientT):   
        laplacianT = laplacianFuncVec(pile.meshTemp, pile.dx, pile.dy, pile.topEdgeOfY)
        laplacianO2 = laplacianFuncVec(pile.meshO2, pile.dx, pile.dy, pile.topEdgeOfY)
        ew = pile.voidFraction
        pCeff = (ew*1.17*1005+(1-ew)*ew*1150*3320)
        alpha = (ew*(0.026)+(1-ew)*(0.3))/pCeff#0.00145 # diffusivity
        dO2 = (0.176/10000)/np.power(273+25, 3/2)*np.power(273+45, 3/2)*ew #https://en.wikipedia.org/wiki/Mass_diffusivity
        Kp = 0.056 #kg/m3
        Ko = 10e-2 #mg/L
        Yo = 1.12 #mol/mol yield rate 
        Yt = 14e6/pCeff #K/kg proportional to O2 consumption
        # evolve non-edge cells
        eatenM = 0
        #for i in range(1, len(pile.meshTemp)-1):
        #        for j in range(1, pile.topEdgeOfY):
        dissolvedO2 = pile.bulkRho/1000*(1-pile.dryFraction)*pile.meshO2/(0.272)/ew*9.3 # mg/L
        Xp = (1.0e-4)*(pile.bulkRho*pile.dryFraction)/(pile.bulkRho*pile.dryFraction+Kp)*dissolvedO2/(dissolvedO2+Ko)*pile.meshX*f1(pile.meshTemp)*dt
        Xm = (7.6e-5) * pile.meshX * f2(pile.meshTemp) * dt
        pile.meshO2 += dO2*laplacianO2*dt - Xp*(0.032)/Yo
        pile.meshTemp += alpha*laplacianT*dt + Xp * (0.032)/Yo * Yt
        dM = Xp/Yo*0.180/6
        eatenM = np.sum(dM)
        pile.meshX += Xp-Xm
                        #if(j==5 and i==5): 
                                #print ("f2(T)", f2(pile.meshTemp[i][j]))
                                #print ("dissolved O2: ", dissolvedO2)
                                #print ("Kp factor: ", (pile.bulkRho*pile.dryFraction)/(pile.bulkRho*pile.dryFraction+Kp))
                                #print ("Xp:", Xp)
                                #print ("Xm:", Xm)
        #print("eatenM:", eatenM)

        #for x in range(1, len(pile.meshTemp)-1):
        #       pile.meshO2[x][0] = pile.meshO2[x][1]
        pile.meshO2[1:-1, 0] = pile.meshO2[1:-1, 1]

        pile.eatMass(eatenM)
        setBoundaryConditions(pile, ambientT)

def setBoundaryConditions(pile, ambientT):
        pile.setBoundaryCondition(pile.meshTemp, ambientT, ambientT, ambientT, ambientT)
        pile.setBoundaryCondition(pile.meshO2, pile.iniO2, pile.iniO2, pile.iniO2, pile.iniO2)
        #for x in range(1, len(pile.meshTemp)-1):
        #        pile.meshO2[x][pile.topEdgeOfY] = pile.iniO2
        pile.meshX[:, pile.topEdgeOfY:]=0
        #pile.meshO2[1:-1][pile.topEdgeOfY] = pile.iniO2
