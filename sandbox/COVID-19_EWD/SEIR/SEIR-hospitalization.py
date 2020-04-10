from scipy.integrate import odeint
import json
import numpy as np
import matplotlib.pyplot as plt
import argparse


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Solve a SEIR-like ODE system"
    )
    parser.add_argument(
        "-o", metavar="FILENAME", type=str, action="store", help="output CSV file", required=True)
    parser.add_argument(
        "-N", metavar="N", type=int, action="store", help="total population", required=True)
    parser.add_argument(
        "-Tinc", metavar="Tinc", type=float, action="store", help="incubation time in days", required=True)
    parser.add_argument(
        "-Tinf", metavar="Tinc", type=float, action="store", help="duration of infectious period in days", required=True)
    parser.add_argument(
        "-pHosp", metavar="pHosp", type=float, action="store", help="probability of hospitalization", required=True)
    parser.add_argument(
        "-Rt", metavar="Rt", type=float, action="store", help="transmission rate", required=True)
    parser.add_argument(
        "-D", metavar="D", type=int, action="store", help="number of days to run the simulation for", required=True)
    parser.add_argument(
        "-I0", metavar="I0", type=int, action="store", help="number of infected on day 0", default=1)
    return parser


# This is so that we can call "json.dumps" on Numpy arrays
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def deriv_(args, y_, t_):
    """ODE system based on the SEIR model"""
    E, I, H, R, S = y_  # exposed, infected, hospitalized, removed, susceptible
    dE_ = (args.Rt / args.Tinf * (I + H) * S / args.N - E / args.Tinc) * 1.0
    dI_ = (E / args.Tinc * (1.0 - args.pHosp) - I / args.Tinf) * 1.0
    dH_ = (E / args.Tinc * args.pHosp - H / args.Tinf) * 1.0
    dR_ = (I + H) / args.Tinf * 1.0
    dS_ = -(args.Rt / args.Tinf) * (I + H) * S / args.N * 1.0
    return dE_, dI_, dH_, dR_, dS_

def solve(args):
    # Boundary conditions and setup
    timeRange_ = np.arange(0.0, args.D, 1.0)
    y0_ = 0.0, args.I0, 0.0, 0.0, args.N
    sol_ = odeint(lambda y, t : deriv_(args, y, t), y0_, timeRange_)
    return (timeRange_, sol_)

def printJSON(t, vars):
    l = vars.T.tolist()
    l.insert(0,t.tolist())
    print(json.dumps(l))

def plot(t, vars):
    plt.plot(t, vars[:, 0], 'b', label='E(t)')
    plt.plot(t, vars[:, 1], 'g', label='I(t)')
    plt.plot(t, vars[:, 2], 'r', label='H(t)')
    # plt.plot(timeRange_, output[:, 3], 'y', label='R(t)')
    # plt.plot(timeRange_, output[:, 4], 'p', label='S(t)')
    # plt.legend(loc='best')
    plt.xlabel('t')
    plt.grid()
    plt.show()

def saveCSV(args, t, vars):
    l = vars.T.tolist()
    l.insert(0,t.tolist())
    a = np.asarray(l).T
    header ="day,exposed,infected,hospitalized,removed,susceptible"
    np.savetxt(args.o,a,delimiter=",",header=header,comments="")

def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
    (t,vars) = solve(args)
    #plot(t,vars)
    #printJSON(t,vars)
    saveCSV(args,t,vars)

if __name__ == "__main__":
    main()