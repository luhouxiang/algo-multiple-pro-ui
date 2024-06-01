# -*- coding: utf-8 -*-
from enum import Enum


EPSINON = 0.00001

def equ_than_0(f):
    return -EPSINON <= f <= EPSINON

def greater_than_0(f):
    return f > EPSINON

def greater_equ_than_0(f):
    return f >= -EPSINON

def less_than_0(f):
    return f < -EPSINON

def less_equ_than_0(f):
    return f <= EPSINON

def lesszero(f):
    return less_than_0(f)

def greatezero(f):
    return greater_than_0(f)

def float_true(f):
    return not equ_than_0(f)


class Trait(Enum):
    NEWLY = 11
    OLDEN = 12
    DIVISION = 51
    OLDEN_EXACT = 22
