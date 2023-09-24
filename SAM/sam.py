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
            (str, set[int], list[PlanningObject])]] = dict()  # represents all parameter bound literals mapped by action
        effA: dict[str, (set[(str, set[int], list[
            PlanningObject])], set[(str, set[int], list[
             PlanningObject])])] = dict()  # dict like preA that holds delete and add biding for each action name
        #  add is 0 index in tuple and delete is 1
        preA: dict[str, set[(str, set[int], list[
            PlanningObject])]] = dict()  # represents  parameter bound literals mapped by action, of pre-cond
        Lifted_preA: [str, set[LearnedLiftedFluent]] = dict()
        # LiftedPreA, LiftedEFF both of them are stets of learned lifted fluents
        types: [str, str] = dict()
        action_triplets: set[SAS] = set()
        learned_lifted_fluents: set[LearnedLiftedFluent] = set()

        # =======================================Initialization of data structures======================================
        def __init__(self, types: [str, str], trace_list: TraceList):
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
                        for f in act.precond.union(act.add, act.delete):   # for every fluent in the acts fluents
                            param_indexes_in_literal: set[int] = set()  # ibitiate a set of ints
                            for obj in act.obj_params:  # for every object in the parameters
                                if f.objects.__contains__(obj):  # if the object is true in fluent then
                                    param_indexes_in_literal.add(act.obj_params.index(obj))  # add obj index to the set
                            self.L_bLA[act.name].add((f.name, param_indexes_in_literal, f.objects))

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
                    param_indexes_in_literal: set[int] = set()
                    for obj in act.obj_params:  # for every object in parameters, if object is in fluent, add its index
                        if k.objects.__contains__(obj):
                            param_indexes_in_literal.add(act.obj_params.index(obj))
                    bla = (fluent_name, param_indexes_in_literal, k.objects)
                    if self.effA.keys().__contains__(act.name):  # if action name exists in dictionary the add
                        if to_add:
                            self.effA[act.name][0].add(bla)  # add it to add effect
                        else:
                            self.effA[act.name][1].add(bla)  # add it to the delete effect

                    else:  # action name not yet on dictionary
                        if to_add:
                            self.effA[act.name] = {{bla}, set()}  # add it to add effect and init set of delete
                        else:
                            self.effA[act.name] = {set(), {bla}}  # add it to the delete effect ant init set of add

        def loop_over_action_triplets(self):
            """implement lines 5-11 in the SAM paper
            calls dd_surely_effects and remove_redundant_preconditions to make pre-con(A) , Eff(A)"""

            for sas in self.action_triplets:  # sas is state-action-state
                self.remove_redundant_preconditions(sas)
                self.add_surely_effects(sas)

        # =======================================finalize and return a model============================================
        def make_lifted_instances(self):
            for action_name, fluent_tuples in self.L_bLA.items():
                param_sorts = []  # Define the param_sorts list based on your data
                act = LearnedLiftedAction(action_name, param_sorts)

                # Iterate through fluent_tuples to create instances of LearnedLiftedFluent and associate them with
                # the action
                for fluent_tuple in fluent_tuples:
                    fluent_name, param_act_inds, objects = fluent_tuple
                    fluent = LearnedLiftedFluent(fluent_name, param_sorts, param_act_inds)

                    # Associate the fluent with the action's preconditions, add, or delete
                    if action_name in self.preA:
                        act.precond.add(fluent)
                    elif action_name in self.effA:
                        act.add.add(fluent)
                    else:
                        act.delete.add(fluent)

        def generate_model(self) -> model.Model:
            pass
            # # step 2 -> initialize effect to empty-set and pre to union off all fluents observed:
            # # note that effect set already initialized to empty set
            # # line 5 we iterate over action triplets for all identical bindings and update effect and pre accordingly
            # self.loop_over_action_triplets()
            #
            # learned_action_set: set[LearnedAction] = set()
            # learned_fluents_set: set[LearnedFluent] = set()
            # # for lifted_action_name in self.lifted_action_groundings.keys():
            # #     learned_act = LearnedAction(lifted_action_name, list()) and add afterwards
            # #     pass
            # for f in self.fluents:
            #    l_f = LearnedFluent(f.name, f.objects)  # I just added all existing fluents, don't know if it's correct
            #     learned_fluents_set.add(l_f)
            #
            # return model.Model(learned_fluents_set, learned_action_set)