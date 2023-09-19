from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, List, Set, Tuple
from warnings import warn

import macq
from nnf import And, Or, Var
from nnf import false as nnffalse

from macq.observation import Observation, ObservedTraceList, PartialObservation
from macq.trace import Action, Fluent, state, action
from macq.utils.pysat import RC2, WCNF, to_wcnf
from macq.extract import LearnedAction, LearnedFluent, Model
from macq.extract.exceptions import IncompatibleObservationToken, InvalidMaxSATModel


class SAM:
    """DESCRIOPTION
    """

    def __new__(cls, types: set, objects: list, ini_state: state, goal: set, T: set):
        """Creates a new Model object.
                Args:
                    types (types set):
                        a set of types of the domain.
                    ini_state (state):
                        the initial state of the lifted domain
                    goal (bool):
                        a set of??? that describes the goal.
                    T (bool):
                        a set of traces from other planning problems in the same domain.

                Raises:
                   ?
                """

    def check_injective_assumption (self, parameters: list[action.PlanningObject], action_identifier):

        object_set: set[action.PlanningObject] = set()
        for p in parameters:
            if isinstance(p, action.PlanningObject):
                if object_set.__contains__(p):
                    raise Exception("parameters of function must all be different due to the injective "
                                    "assumption\naction identifier: " + action_identifier)
                else:
                    object_set.add(p)
            else:
                raise TypeError("parameter of action was not an object\naction identifier: " + action_identifier)

