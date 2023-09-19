from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, List, Set, Tuple
from warnings import warn

import macq
from nnf import And, Or, Var
from nnf import false as nnffalse

from macq.observation import Observation, ObservedTraceList, PartialObservation
from macq.trace import Action, Fluent, state
from macq.utils.pysat import RC2, WCNF, to_wcnf
from macq.extract import LearnedAction, LearnedFluent, Model
from macq.extract.exceptions import IncompatibleObservationToken, InvalidMaxSATModel



