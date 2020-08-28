#!/usr/bin/python
from gurobipy import *
from gurobifun import *

N = 128 # the words size.

# !SECTION! Modelling tinyJambu constraints
# =======================

def stateUptLin(mod, stin, stout, Ands, r):
    """ Add the simple model onstraints of a single round of TinyJambu with keeping tracks of Ands chains.
        Parameters:
        mod     - the Model
        stin    - the variables of the input state
        stout   - the variables of the output state
        And     - the And chains
        r       - the current round number
    """
    objectiveFun = []

    objectiveFun += [stin[0]]
    mod.addConstr(stout[127] == stin[0])
    j = r%15
    approx = [get_new_var(mod) for _ in xrange(2)]
    Ands[j] += [approx + [stin[0]]]
    for i in xrange(2):
        mod.addConstr(approx[i] <= stin[0]) #Fix approx to 0 when not needed.
    for i in xrange(N-1):
        if(i == 84 or i == 69):
            addGenConstrXor(mod, [stout[i], stin[i+1], approx[ 0 if i == 69 else 1 ]], False)
        elif(i == 90 or i == 46):
            addGenConstrXor(mod, [stin[0], stin[i+1], stout[i]], False)
        else:
            mod.addConstr(stout[i] == stin[i+1])
    return objectiveFun

def chainedAndConstr(mod, Ands):
    """ Add constraints of the refined model on top of the simple model
        using the Ands chains.
    """
    L = len(Ands)
    negativeFun = []

    temp = get_new_var(mod)
    mod.addGenConstrAnd(temp, [Ands[0][2], Ands[1][2]])
    mod.addConstr(Ands[0][0] <= Ands[1][1] + 1 - temp)
    mod.addConstr(Ands[0][0] >= Ands[1][1] - 1 + temp)
    negativeFun += [temp] #we have correlation so we deduce 1.

    for i in xrange(1,L-1):
        temp = get_new_var(mod)
        mod.addGenConstrAnd(temp, [invert_variable(mod,negativeFun[-1]), Ands[i][2], Ands[i+1][2]])
        mod.addConstr(Ands[i][0] <= Ands[i+1][1] + 1 - temp)
        mod.addConstr(Ands[i][0] >= Ands[i+1][1] - 1 + temp)

        negativeFun += [temp] #we have correlation so we deduce 1.

    return negativeFun

def printSols():
    """ Print all solutions (set by mod.Params.PoolSolutions in main).
    """
    print( str(int(quicksum(objFuns).getValue())) + " active gates - " + str(int(quicksum(negFuns).getValue())) + " correlated")
    nSol = mod.SolCount
    for sol in range(nSol):
        mod.Params.SolutionNumber = sol
        print( "Solution number "+str(sol+1)+ ", " + str(int(mod.PoolObjVal)) + " score.")
        for r in range(0,len(states)-1,128) + [len(states)-1]:
            print( "m"+ str(r) +"  = 0x{:08x}, 0x{:08x}, 0x{:08x}, 0x{:08x}".format(variables_block_to_int(states[r][96:128]), variables_block_to_int(states[r][64:96]), variables_block_to_int(states[r][32:64]), variables_block_to_int(states[r][0:32])))
        print( "========")
    mod.Params.SolutionNumber = 0

# !SECTION! Main
# =======================

if __name__ == "__main__":
    # building MILP model
    mod = Model("test")
    nbrounds = 256  # number of rounds
    mod.Params.PoolSearchMode = 2 #def: 0, sol first: 1, best sols: 2
    mod.Params.Threads = 4
    mod.Params.PoolSolutions = 50

    # Create state variables for every rounds.
    states = [get_new_variables_block(mod, N) for r in xrange(nbrounds+1)]
    # Initialize the variable lists for the sum to be optimized.
    objFuns = []
    # Initialize empty And chains.
    Ands = [[] for _ in xrange(15)]

    # Add the simple model constraints and objective function.
    for r in xrange(nbrounds):
        objFuns += stateUptLin(mod, states[r], states[r+1], Ands, r)
    
    # Add refined model constraints and create a negative objective function (number of correlations).
    negFuns = []
    for i in xrange(15):
        negFuns += chainedAndConstr(mod, Ands[i])

    # Add constraints on the relevant linear trail (Type 1, 2, 3, 4).
    not_all_zeros_constraint(mod, states[0])

    for i in range(0,N-64) + range(N-32,N):
        mod.addConstr(states[0][i] == 0)    # set some input mask to 0.
        mod.addConstr(states[-1][i] == 0)   # set some output mask to 0.

    #dstart = 0x02400004081220010040102040000080
    #dend   = 0x00000000000000010000000000000000
    #for i in xrange(N):
    #    mod.addConstr(states[0][i] == (dstart >> i)&1)
    #    mod.addConstr(states[-1][i] == (dend >> i)&1)

    # Set objecive functions as sum of active AND gates minus correlations.
    mod.setObjective(quicksum(objFuns)- quicksum(negFuns))

    # Optimize.
    mod.optimize()
    printSols()