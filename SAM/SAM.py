from macq.trace import Action, Fluent, state, action, PlanningObject, Trace, State, SAS, TraceList
from macq.extract import model, LearnedAction, LearnedFluent


def check_injective_assumption(parameters: list[PlanningObject], action_name):
    """meant to check that all grounded actions parameters are bound to different objects"""
    object_set: set[action.PlanningObject] = set()
    for p in parameters:
        if isinstance(p, action.PlanningObject):
            if object_set.__contains__(p):
                raise Exception("parameters of function must all be different due to the injective "
                                "assumption\naction identifier: " + action_name)
            else:
                object_set.add(p)
        else:
            raise TypeError("parameter of action was not an object\naction identifier: " + action_name)


class SAMgenerator:
    """DESCRIPTION
    """
    fluents: set[Fluent]  # list of all fluents collected from all traces
    objects: list[PlanningObject] = list()
    states: set[State] = set()
    trace_list: TraceList
    lifted_action_groundings: dict[
        str, set[Action]] = dict()  # dictionary that maps by Lifted action name all groundings
    effA: [str, set[Fluent]] = dict()  # dictionary that maps by action name, to set of fluents in effect
    preA: [str, set[Fluent]] = dict()  # dictionary that maps by action name, to set of fluents in effect
    types: set[str] = set()
    action_triplets: set[SAS] = set()

    def __init__(self, types: set[str], objects: list[PlanningObject], trace_list: TraceList):
        """Creates a new SAMgenerator instance.
                Args:
                    types (str set):
                        a set of types of the domain.
                    objects (list[Planning object]):
                        a list of planning object in the domain.
                    trace_list(TraceList):
                        an object holding a list of traces from the same domain.

                Raises:
                   ?
                """
        self.types = types
        self.trace_list = trace_list
        self.objects = objects
        self.fluents = self.trace_list.get_fluents()
        # step 2 -> initialize effect to empty-set and pre to union off all fluents observed:
        self.init_preA()
        # note that effect set already initialized to empty set
        for trace in trace_list.traces:
            for act in trace.actions:
                self.action_triplets.union(set(trace.get_sas_triples(act)))
        # line 5 we iterate over action triplets for all identical bindings and update effect and pre accordingly
        self.loop_over_action_triplets()

    # =======================================Initialization of data structures==========================================

    def map_actions_by_name(self):
        """a method that maps all groundings \'a\' of Action A to the appropriate set by name of the action"""
        for t in self.trace_list.traces:
            for act in t.actions:
                if isinstance(act, Action):
                    if self.lifted_action_groundings.__contains__(act.name):
                        self.lifted_action_groundings[act.name].add(act)
                    else:
                        self.lifted_action_groundings[act.name] = {act}

    # =======================================algorithm logic============================================================

    def init_preA(self):  # intialization of pre-condition set should include all preconditions based on line 4 in paper
        """initializes a dict and unionize all parameter-bound literals"""
        for A in self.lifted_action_groundings.keys():
            for grounded_act in self.lifted_action_groundings[A]:
                if self.preA.keys().__contains__(A):
                    self.preA.get(A).union(grounded_act.precond, grounded_act.add, grounded_act.delete)
                else:
                    self.preA[A] = grounded_act.precond

    def remove_redundant_preconditions(self, sas: SAS):  # based on lines 6 to 8 in paper
        """removes all parameter-bound literals that are not pre-conditions"""
        pass

    def add_surely_effects(self, sas: SAS):  # based on lines 9 to 11 in paper
        """add all parameter-bound literals that are surely an effect"""
        pass

    def loop_over_action_triplets(self):
        """implement lines 5-11 in the SAM paper"""
        for act_tri in self.action_triplets:
            self.remove_redundant_preconditions(act_tri)
            self.add_surely_effects(act_tri)

# =======================================finalize and return a model====================================================
    def generate_model(self) -> model.Model:
        learned_action_set: set[LearnedAction] = set()
        learned_fluents_set: set[LearnedFluent] = set()
        for lifted_action_name in self.lifted_action_groundings.keys():
            # learned_act = LearnedAction(lifted_action_name, list()) and add afterwards
            pass
        for f in self.fluents:
            l_f = LearnedFluent(f.name, f.objects)  # I just added all existing fluents, don't know if it's correct
            learned_fluents_set.add(l_f)
            pass
        return model.Model(learned_fluents_set, learned_action_set)
