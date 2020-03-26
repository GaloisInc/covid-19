
from scipy.integrate import odeint
import json
import numpy as np
import matplotlib.pyplot as plt
from math import sin

# This is so that we can call "json.dumps" on Numpy arrays
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

# User defined constants
N = 7000000.0
Tinc = 5.2
Tinf = 2.9
pHosp = 0.2
Rt = 2.2

# The ODE system
def deriv_(y_, t_):
    E, I, H, R, S = y_
    dE_ = (Rt / Tinf * (I + H) * S / N - E / Tinc) * 1.0
    dI_ = (E / Tinc * (1.0 - pHosp) - I / Tinf) * 1.0
    dH_ = (E / Tinc * pHosp - H / Tinf) * 1.0
    dR_ = (I + H) / Tinf * 1.0
    dS_ = -(Rt / Tinf) * (I + H) * S / N * 1.0
    return dE_, dI_, dH_, dR_, dS_

# Boundary conditions and setup
timeRange_ = np.arange(0.0, 200.0, 1.0)
y0_ = 0.0, 1.0, 0.0, 0.0, 7000000.0
output = odeint(deriv_, y0_, timeRange_).T



print(json.dumps(output, cls=NumpyEncoder))
