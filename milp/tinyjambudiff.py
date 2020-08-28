#!/usr/bin/python
from gurobipy import *
from gurobifun import *

N = 128 # the words size.

# !SECTION! Modelling tinyJambu constraints
# =======================

def stateUptDiff(mod, stin, stout, And, X, r, nbr):
    """ Add the simple model onstraints of nbr rounds of TinyJambu with keeping tracks of Ands chains.
        Parameters:
        mod     - the Model
        stin    - the variables of the input state
        stout   - the variables of the output state
        And     - the And chains
        X       - the variables of the respective And chains
        r       - the current round number
        nbr     - the number of rounds between stin and stout
    """
    objectiveFun = []

    nand = get_new_variables_block(mod, nbr)
    temp = get_new_variables_block(mod, nbr)
    for i in xrange(nbr):
        mod.addConstr(nand[i] <= stin[85+i] + stin[70+i]) #if no diff in x and y then no diff in xy
        mod.addGenConstrOr(temp[i], [stin[85+i], stin[70+i]])
        addGenConstrXor(mod,[stout[i-nbr], stin[91+i], stin[47+i], stin[i], nand[i]] ,False)
        j = (r+i)%15
        And[j] += [nand[i]]
        X[j] += [stin[85+i]]

    objectiveFun += temp

    for i in xrange(N-nbr):
        mod.addConstr(stout[i] == stin[i+nbr])
    return objectiveFun

def chainedAndConstr(mod, Ands, Xs):
    """ Add constraints of the refined model on top of the simple model
        using the Ands chains.
    """
    negativeFun = []
    L = len(Ands)
    assert L == len(Xs)-1, "And chains not right length."

    for i in xrange(L-1):
        temp = get_new_var(mod)
        mod.addGenConstrAnd(temp, [Xs[i], invert_variable(mod,Xs[i+1]), Xs[i+2]])
        mod.addConstr(Ands[i] - Ands[i+1] <= 1 - temp)
        mod.addConstr(Ands[i+1] - Ands[i] <= 1 - temp) #if x=1, y=0, z=1 then xy=yz
        
        negativeFun += [temp] # we have correlation so we deduce 1.
    return negativeFun

def printSols():
    """ Print all solutions (set by mod.Params.PoolSolutions in main).
    """
    print( str(int(quicksum(objFuns).getValue())) + " active gates - " + str(int(quicksum(negFuns).getValue())) + " correled")
    nSol = mod.SolCount
    for sol in range(nSol):
        mod.Params.SolutionNumber = sol
        # printing the differences found
        print( "Solution number "+str(sol+1)+ ", " + str(int(mod.PoolObjVal)) + " score.")
        for r in range(0,len(states)-1,4) + [len(states)-1]:
            print( "d"+ str(r*32) +"  = 0x{:08x}, 0x{:08x}, 0x{:08x}, 0x{:08x}".format(variables_block_to_int(states[r][96:128]), variables_block_to_int(states[r][64:96]), variables_block_to_int(states[r][32:64]), variables_block_to_int(states[r][0:32])))
        print( "========")
    mod.Params.SolutionNumber = 0

# !SECTION! Main
# =======================

if __name__ == "__main__":
    # building MILP model
    mod = Model("test")
    nbrounds = 128 # number of rounds
    mod.Params.PoolSearchMode = 1 #default: 0, sol first: 1, best sols: 2
    mod.Params.Threads = 4
    mod.Params.PoolSolutions = 50
    
    # Create state variables for every 32 rounds.
    states = [get_new_variables_block(mod, N) for r in xrange((nbrounds-1)//32+2)]
    # Initialize the variable lists for the sum to be optimized.
    objFuns = []
    # Initialize empty And chains and the head of the associated variables.
    Ands = [[] for _ in xrange(15)]
    Xs = [[states[0][i]] for i in xrange(70, 85)]

    # Add simple model constraints and objective function.
    for r in xrange((nbrounds-1)//32):
        objFuns += stateUptDiff(mod, states[r], states[r+1], Ands, Xs, r*32, 32)
    objFuns += stateUptDiff(mod, states[-2], states[-1], Ands, Xs, (nbrounds-1) - (nbrounds-1)%32, 1 + (nbrounds-1)%32)

    # Add refined model constraints and create a negative objective function (number of correlations).
    negFuns = []
    for i in xrange(15):
        negFuns += chainedAndConstr(mod, Ands[i], Xs[i])

    # Add constraints on the relevant differential path (Type 1, 2, 3, 4).
    not_all_zeros_constraint(mod, states[0])
    for i in xrange(N-32):
        mod.addConstr(states[0][i] == (0 >> i)&1)       # set some input diff to 0.
        #mod.addConstr(states[-1][i] == (0 >> i)&1)     # set some output diff to 0.

    #d0  = 0x80000000200100000000009200000500
    #d128  = 0x00000000200000000000400000000004
    #d256  = 0x00000000200000000000000000000000
    #d384  = 0x81020000200010000000408000000004
    #for i in xrange(N):
    #    mod.addConstr(states[0][i] == (d0 >> i)&1)
    #    mod.addConstr(states[-1][i] == (d384 >> i)&1)

    # Set objecive functions as sum of active AND gates minus correlations.
    mod.setObjective(quicksum(objFuns) - quicksum(negFuns))

    # Optimize.
    mod.optimize()
    printSols()