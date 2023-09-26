from macq.trace import Action, Fluent, action, PlanningObject, State, SAS, TraceList
from macq.extract import model, LearnedLiftedFluent, LearnedLiftedAction


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


class SAM:
    def __new__(cls, types: dict[str, str], objects: list[PlanningObject], trace_list: TraceList):
        """Creates a new SAM instance.
                            Args:
                                types (dict str -> str):
                                    a dic mapping each type to its super type, for example: [mazda, car].
                                    means mazda type is type of car type
                                trace_list(TraceList):
                                    an object holding a list of traces from the same domain.

                            :return:
                               a model based on SAM learning
                            """
        sam_generator: SAM.SAMgenerator = SAM.SAMgenerator(types, trace_list)
        return sam_generator.generate_model()

    class SAMgenerator:
        """DESCRIPTION
        """
        fluents: set[Fluent]  # list of all fluents collected from all traces
        trace_list: TraceList
        L_bLA: dict[str, set[
            (str, list[str], set[int])]] = dict()  # represents all parameter bound literals mapped by action
        effA_add: dict[str, set[
            (str, list[str], set[int])]] = dict()  # dict like preA that holds delete and add biding for each action
        # name
        effA_delete: dict[str, set[
            (str, list[str], set[int])]] = dict()  # dict like preA that holds delete and add biding for each action
        # name
        #  add is 0 index in tuple and delete is 1
        preA: dict[str, set[(str, list[int], list[
            str])]] = dict()  # represents  parameter bound literals mapped by action, of pre-cond
        # LiftedPreA, LiftedEFF both of them are stets of learned lifted fluents
        types: str = dict()
        action_triplets: set[SAS] = set()
        learned_lifted_fluents: set[LearnedLiftedFluent] = set()
        learned_lifted_action: set[LearnedLiftedAction] = set()
        action_2_sort: dict[str, list[str]] = dict()  # TODO use when knowing how to sort action

        # =======================================Initialization of data structures======================================
        def __init__(self, types: str, trace_list: TraceList ,action_2_sort: dict[str, list[str]]):
            """Creates a new SAMgenerator instance.
                    Args:
                        types (str set):
                            a set of types of the domain.
                        trace_list(TraceList):
                            an object holding a list of traces from the same domain.

                    Raises:
                       ?
                    """
            self.types = types
            self.trace_list = trace_list
            self.fluents = self.trace_list.get_fluents()
            self.update_action_triplets()
            self.collect_L_bLA()
            self.preA = self.L_bLA.copy()
            self.action_2_sort = action_2_sort

        def update_action_triplets(self):
            for trace in self.trace_list.traces:
                for act in trace.actions:
                    self.action_triplets.update(set(trace.get_sas_triples(act)))

        # =======================================algorithm logic========================================================

        def collect_L_bLA(self):
            """collects all parameter bound literals and maps them based on action name
            values of dict is a set[(fluent.name, set[indexes of parameters that fluent applies on])]"""
            for trace in self.trace_list.traces:  # for every trace in the trace list
                for act in trace.actions:  # for every act in the trace
                    if isinstance(act, Action):
                        if not self.L_bLA.keys().__contains__(act.name):  # if act name not already id the dictionary
                            self.L_bLA[act.name] = set()  # initiate its set
                        for f in act.precond.union(act.add, act.delete):  # for every fluent in the acts fluents
                            param_indexes_in_literal: list[int] = list()  # initiate a set of ints
                            sorts: list[str] = list()
                            for obj in act.obj_params:  # for every object in the parameters
                                sorts.append(obj.obj_type)
                                if f.objects.__contains__(obj):  # if the object is true in fluent then
                                    param_indexes_in_literal.append(act.obj_params.index(obj))  # append obj index to
                                    # the list
                            self.L_bLA[act.name].add((f.name, sorts, param_indexes_in_literal))

        def remove_redundant_preconditions(self, sas: SAS):  # based on lines 6 to 8 in paper
            """removes all parameter-bound literals that there groundings are not pre-state"""
            act: Action = sas.action
            pre_state: State = sas.pre_state
            for param_bound_lit in self.preA[act.name]:
                fluent = Fluent(param_bound_lit[0], param_bound_lit[2])
                if not pre_state.fluents.keys().__contains__(fluent) or not pre_state.fluents[fluent]:  # remove if
                    # unbound or if not true, means, preA contains at the end only true value fluents
                    self.preA[act.name].remove(param_bound_lit)

        def add_surely_effects(self, sas: SAS):  # based on lines 9 to 11 in paper
            """add all parameter-bound literals that are surely an effect"""
            act: Action = sas.action
            pre_state: State = sas.pre_state.copy()
            post_state: State = sas.post_state.copy()
            for k, v in post_state.fluents.items():
                if (not pre_state.fluents.keys().__contains__(k)) or post_state.fluents[k] != pre_state[k]:
                    to_add = post_state.fluents[k]
                    fluent_name = k.name
                    param_indexes_in_literal: list[int] = list()
                    for obj in act.obj_params:  # for every object in parameters, if object is in fluent, add its index
                        if k.objects.__contains__(obj):
                            param_indexes_in_literal.append(act.obj_params.index(obj))
                    bla = (fluent_name, k.objects, param_indexes_in_literal)
                    if to_add:
                        if self.effA_add.keys().__contains__(act.name):  # if action name exists in dictionary then add
                            self.effA_add[act.name].add(bla)  # add it to add effect
                        else:
                            self.effA_add[act.name] = {{bla}, set()}
                    else:
                        if self.effA_delete.keys().__contains__(act.name):
                            self.effA_delete[act.name].add(bla)  # add it to the delete effect
                        else:
                            self.effA_delete[act.name] = {set(), {bla}}  # add it to the delete effect ant init set

        def loop_over_action_triplets(self):
            """implement lines 5-11 in the SAM paper
            calls dd_surely_effects and remove_redundant_preconditions to make pre-con(A) , Eff(A)"""

            for sas in self.action_triplets:  # sas is state-action-state
                self.remove_redundant_preconditions(sas)
                self.add_surely_effects(sas)

        # =======================================finalize and return a model============================================
        def make_act_sorts(self):
            # TODO change method when knowing how to type inference
            pass

        def make_act_lifted_fluent_set(self, act_name,
                                       keyword="PRE" | "ADD" | "DELETE") -> (
                set)[LearnedLiftedFluent]:
            """ make the fluent set for an action based on the keyword provided"""
            learned_fluents_set = set()
            if keyword == "PRE":
                for fluents_set in self.preA[act_name]:
                    for fluent_info in fluents_set:
                        pre_lifted_fluent = LearnedLiftedFluent(fluent_info[0], fluent_info[1], fluent_info[2])
                        learned_fluents_set.add(pre_lifted_fluent)

            if keyword == "ADD":
                for fluents_set in self.effA_add[act_name]:
                    for fluent_info in fluents_set:
                        pre_lifted_fluent = LearnedLiftedFluent(fluent_info[0], fluent_info[1], fluent_info[2])
                        learned_fluents_set.add(pre_lifted_fluent)
            if keyword == "DELETE":
                for fluents_set in self.effA_add[act_name]:
                    for fluent_info in fluents_set:
                        pre_lifted_fluent = LearnedLiftedFluent(fluent_info[0], fluent_info[1], fluent_info[2])
                        learned_fluents_set.add(pre_lifted_fluent)
            return learned_fluents_set

        def make_learned_fluent_set(self):
            """ unionize all fluents of action to make a set of all fluents in domain"""
            for lift_act in self.learned_lifted_action:
                self.learned_lifted_fluents.update(lift_act.precond, lift_act.add, lift_act.delete)

        def make_lifted_instances(self):
            """makes the learned lifted and learned fluents set based on the collected data"""
            # {act_name:{pre:set,add:set,delete:set}}
            for action_name, fluent_tuples in self.L_bLA.items():
                learned_act_fluents: dict[str, set[LearnedLiftedFluent]] = dict()
                learned_act_fluents["precond"] = self.make_act_lifted_fluent_set(action_name, keyword="PRE")
                learned_act_fluents["add"] = self.make_act_lifted_fluent_set(action_name, keyword="ADD")
                learned_act_fluents["delete"] = self.make_act_lifted_fluent_set(action_name, keyword="DELETE")
                lifted_act = LearnedLiftedAction(action_name, self.action_2_sort[action_name],
                                                 precond=learned_act_fluents["precond"],
                                                 add=learned_act_fluents["add"], delete=learned_act_fluents["delete"])
                self.learned_lifted_action.add(lifted_act)

        def generate_model(self) -> model.Model:
            return model.Model(self.learned_lifted_fluents, self.learned_lifted_action)
