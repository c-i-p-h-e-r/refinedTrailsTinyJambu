from gurobipy import *
# used to have a unique string identifier for each block of
# variables. It is incremented each time a new block is created.
VAR_NAME_ID = 0

def get_new_var(mod):
    global VAR_NAME_ID
    result = mod.addVar(vtype=GRB.BINARY, name="{:d}".format(VAR_NAME_ID))
    VAR_NAME_ID += 1
    return result

def get_new_variables_block(mod, N):
    """Returns a list of N variables that can then be used to construct a
    pysciopt model.

    """
    return [get_new_var(mod) for _ in xrange(0, N)]

def variables_block_to_int(vars):
    return sum(int(vars[i].xn) << i for i in xrange(len(vars)))

def variables_block_to_intx(vars):
    return sum(int(vars[i].x) << i for i in xrange(len(vars)))

def xor_var(mod, xpy, x, y):
    """ xpy = x xor y """
    mod.addConstr(xpy >= x - y)
    mod.addConstr(xpy >= y - x)
    mod.addConstr(xpy <= x + y)
    mod.addConstr(xpy <= 2 - x - y)

def addGenConstrXor(mod, vals, tar):
    """ Add a xor constraint to mod """
    if(len(vals)) == 2:
        xor_var(mod, tar, vals[0], vals[1])
        return
    if(len(vals)) == 3:
        if tar:
            xor_var(mod, vals[0], vals[1], invert_variable(mod, vals[2]))
        else:
            xor_var(mod, vals[0], vals[1], vals[2])
        return
    somme = get_new_var(mod)
    xor_var(mod, somme, vals[0], vals[1])
    addGenConstrXor(mod, [somme] + vals[2:], tar)
    return

def xor_variables(mod, x, dx):
    """Returns variables that are the xor of the two inputs.
    
    """
    sum_xdx = get_new_variables_block(mod, len(x))
    for i in xrange(0,len(x)):
        addGenConstrXor(mod,[sum_xdx[i], x[i], dx[i]], 0)
    return sum_xdx

def invert_variable(mod, x):
    """Returns a binary variable that is not(x).
    
    """
    not_x = get_new_var(mod)
    mod.addConstr(not_x == 1 - x)
    return not_x

def not_all_zeros_constraint(mod, x):
    """Adds the constraint that there exists i s.t. x[i] != 0 .
    
    """
    mod.addConstr(quicksum(x) >= 1)

def mask_constraints(mod, x, mask):
    """Adds the constraint that x <= y in the sens x&y = x .
    
    """
    for i in xrange(0, len(x)):
        mod.addConstr(x[i] <= mask[i])

def sumL(L):
    r = []
    for i in L:
        r += i
    return r