from macq.trace import Action, Fluent, action, PlanningObject, State, SAS, TraceList, Trace
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


class SAMgenerator:
    """DESCRIPTION
    an object that handles all traces data and manipulates it in order to generate a model based on SAM algorithm
    """
    fluents: set[Fluent] = set()  # list of all fluents collected from all traces
    trace_list: TraceList = TraceList()
    L_bLA: dict[str, list[
        (str, list[str], set[int])]] = dict()  # represents all parameter bound literals mapped by action
    effA_add: dict[str, list[
        (str, list[str], set[int])]] = dict()  # dict like preA that holds delete and add biding for each action
    # name
    effA_delete: dict[str, list[
        (str, list[str], set[int])]] = dict()  # dict like preA that holds delete and add biding for each action
    # name
    #  add is 0 index in tuple and delete is 1
    preA: dict[str, list[
        (str, list[str], set[int])]] = dict() # represents  parameter bound literals mapped by action, of pre-cond
    # LiftedPreA, LiftedEFF both of them are stets of learned lifted fluents
    types: set[str] = set()
    action_triplets: set[SAS] = set()
    learned_lifted_fluents: set[LearnedLiftedFluent] = set()
    learned_lifted_action: set[LearnedLiftedAction] = set()
    action_2_sort: dict[str, list[str]] = dict()  # TODO use when knowing how to sort action

    # =======================================Initialization of data structures======================================
    def __init__(self, types: set[str] = None, trace_list: TraceList = None,
                 action_2_sort: dict[str, list[str]] = None):
        """Creates a new SAMgenerator instance.
               Args:
                    types (dict str -> str):
                        a dic mapping each type to its super type, for example: [mazda, car].
                        means mazda type is type of car type
                    trace_list(TraceList):
                        an object holding a list of traces from the same domain.
                    action_2_sort(dict str -> list[str])
                """
        self.trace_list = trace_list
        if types is not None:
            self.types = types
        if trace_list is not None:
            self.trace_list = trace_list
            self.fluents = self.trace_list.get_fluents()
            self.update_action_triplets(self.trace_list.traces)
            self.action_2_sort = action_2_sort
            self.update_L_bLA(trace_list.traces)

    def make_act_sorts(self):
        """sorts all actions parameter types"""
        # TODO change method when knowing how to type inference
        pass

    # =======================================UPDATE FUNCTIONS========================================================
    def update_action_triplets(self, traces: list[Trace]):
        for trace in traces:
            for act in trace.actions:
                self.action_triplets.update(set(trace.get_sas_triples(act)))

    def update_trace_list(self, trace_list: TraceList):
        for trace in trace_list.traces:
            self.trace_list.insert(trace_list.__len__(), trace)
        self.update_action_triplets(trace_list.traces)
        self.update_L_bLA(trace_list.traces)

    def update_L_bLA(self, traces: list[Trace]):#0-> f_name 1-> sorts of action -> index of fluent sort
        """collects all parameter bound literals and maps them based on action name
                values of dict is a set[(fluent.name, set[indexes of parameters that fluent applies on])]"""
        for trace in traces:  # for every trace in the trace list
            for act in trace.actions:  # for every act in the trace
                if isinstance(act, Action):
                    if not self.L_bLA.keys().__contains__(act.name):  # if act name not already id the dictionary
                         self.L_bLA[act.name] = list()  # initiate its set

                    a: set[Fluent] = set() if act.precond is None else act.precond
                    b: set[Fluent] = set() if act.add is None else act.add
                    c: set[Fluent] = set() if act.delete is None else act.delete
                    f_set = set().union(a, b, c)
                    for f in f_set:  # for every fluent in the acts fluents
                        param_indexes_in_literal: list[int] = list()  # initiate a set of ints
                        sorts: list[str] = list()
                        i: int = 0
                        for obj in act.obj_params:  # for every object in the parameters
                            # TODO change when knowing how to sort types
                            if f.objects.__contains__(obj):  # if the object is true in fluent then
                                param_indexes_in_literal.append(i)  # append obj index to
                                sorts.append(self.action_2_sort[act.name].__getitem__(i))
                                # the list
                            i += 1
                            # for j in range(sorts.__len__()):
                            #     if not param_indexes_in_literal.__contains__(j):
                            #         sorts.pop(i-1)
                        self.L_bLA[act.name].append((f.name, sorts, param_indexes_in_literal))
        self.preA = self.L_bLA.copy()

    def update_action_2_sort(self, action_2_sort: dict[str, list[str]]):
        """inserts key and value, replaces value of key already if key already in dict"""
        self.action_2_sort.update(action_2_sort)

    # =======================================ALGORITHM LOGIC========================================================
    def remove_redundant_preconditions(self, sas: SAS):  # based on lines 6 to 8 in paper
        """removes all parameter-bound literals that there groundings are not pre-state"""
        act: Action = sas.action
        pre_state: State = sas.pre_state
        for param_bound_lit in self.preA[act.name]:
            fluent = Fluent(param_bound_lit[0], [obj for obj in act.obj_params if param_bound_lit[2].__contains__(act.obj_params.index(obj))])  # make a fluent instance so we can use eq function
            if not pre_state.fluents.keys().__contains__(fluent) or not pre_state.fluents[fluent]:  # remove if
                # unbound or if not true, means, preA contains at the end only true value fluents
                self.preA[act.name].remove(param_bound_lit)

    def add_surely_effects(self, sas: SAS):  # based on lines 9 to 11 in paper
        """add all parameter-bound literals that are surely an effect"""
        act: Action = sas.action
        # add all add_effects of parameter bound literals
        self.add_literal_binding_to_eff(sas.post_state, sas.pre_state, act, add_delete="add")
        # add all delete_effects of parameter bound literals
        self.add_literal_binding_to_eff(sas.pre_state, sas.post_state, act, add_delete="delete")

    def add_literal_binding_to_eff(self, s1: State, s2: State, act: Action,
                                   add_delete="add"):
        """gets all fluents in the difference of s1-s2 and add all binding that
           appears in difference to self.eff_'add_delete'[act.name]
           Args:
                    s1 (State):
                        the state on the left side of the difference
                    s2(State):
                        the state on the right side of the difference.
                    act(Action):
                        the action of the effect
                    add_delete(str):
                        if ="add" it adds literal binding to add_effect
                        if ="delete" it adds literal binding to the delete_effect
           """
        for k, v in s1.fluents.items():
            if (not (s2.keys().__contains__(k) and s2.__getitem__(k) == v)) and v:
                param_indexes_in_literal: list[int] = list()
                fluent_name = k.name
                sorts: list[str] = list()
                i: int = 0
                for obj in act.obj_params:  # for every object in parameters, if object is in fluent, add its index
                    # TODO change when knowing how to sort types
                    if k.objects.__contains__(obj):
                        param_indexes_in_literal.append(i)
                        sorts.append(self.action_2_sort.get(act.name).__getitem__(i))
                    i += 1
                    # for j in range(sorts.__len__()):
                    #     if not param_indexes_in_literal.__contains__(j):
                    #         sorts.pop(i-1)
                bla: tuple[str, list[str], list[int]] = (fluent_name, sorts, param_indexes_in_literal)
                if add_delete == "delete":
                    if self.effA_delete.keys().__contains__(act.name):  # if action name exists in dictionary
                        # then add
                        self.effA_delete[act.name].append(bla)  # add it to add effect
                    else:
                        self.effA_delete[act.name] = [bla]

                if add_delete == "add":
                    if self.effA_add.keys().__contains__(
                            act.name):  # if action name exists in dictionary then add
                        self.effA_add[act.name].append(bla)  # add it to add effect
                    else:
                        self.effA_add[act.name] = [bla]

    def loop_over_action_triplets(self):
        """implement lines 5-11 in the SAM paper
        calls dd_surely_effects and remove_redundant_preconditions to make pre-con(A) , Eff(A)"""

        for sas in self.action_triplets:  # sas is state-action-state
            self.remove_redundant_preconditions(sas)
            self.add_surely_effects(sas)

    # =======================================finalize and return a model============================================
    def make_act_lifted_fluent_set(self, act_name: str,
                                   keyword="PRE") -> (
            set)[LearnedLiftedFluent]:
        """ make the fluent set for an action based on the keyword provided
        Args:
                    act_name (str):
                        the state on the left side of the difference
                    keyword(str):
                        if "PRE" makes all lifted preconditions for action.
                        if "ADD" makes all lifted add effects for action
                        if "DELETE" makes all lifted delete effects for action
                    """
        learned_fluents_set = set()
        if keyword == "PRE":
            for fluents_tuple in self.preA[act_name]:
                lifted_fluent = LearnedLiftedFluent(fluents_tuple[0], fluents_tuple[1], fluents_tuple[2])
                learned_fluents_set.add(lifted_fluent)

        if keyword == "ADD":
            for fluents_tuple in self.effA_add.get(act_name):
                lifted_fluent = LearnedLiftedFluent(fluents_tuple[0], fluents_tuple[1], fluents_tuple[2])
                learned_fluents_set.add(lifted_fluent)
        if keyword == "DELETE":
            for fluents_tuple in self.effA_delete[act_name]:
                lifted_fluent = LearnedLiftedFluent(fluents_tuple[0], fluents_tuple[1], fluents_tuple[2])
                learned_fluents_set.add(lifted_fluent)
        return learned_fluents_set

    def make_learned_fluent_set(self):
        """ unionize all fluents of action to make a set of all fluents in domain"""
        for lift_act in self.learned_lifted_action:
            self.learned_lifted_fluents.update(set() if lift_act.precond is None else lift_act.precond,
                                               set() if lift_act.add is None else lift_act.add,
                                               set() if lift_act.delete is None else lift_act.delete)

    def make_lifted_instances(self):
        """makes the learned lifted and learned fluents set based
          on the collected data in add,delete and pre dicts"""
        # {act_name:{pre:set,add:set,delete:set}}
        # for each action that was observed do:
        for action_name in self.L_bLA.keys():
            learned_act_fluents: dict[str, set[LearnedLiftedFluent]] = dict()
            # make all action's pre-condition fluents and add to set
            learned_act_fluents["precond"] = self.make_act_lifted_fluent_set(action_name, keyword="PRE")
            # make all action's add_eff fluents and add to set
            learned_act_fluents["add"] = self.make_act_lifted_fluent_set(action_name, keyword="ADD")
            # make all action's delete_eff fluents and add to set
            learned_act_fluents["delete"] = self.make_act_lifted_fluent_set(action_name, keyword="DELETE")
            # make learned lifted action instance
            lifted_act = LearnedLiftedAction(action_name, self.action_2_sort[action_name],
                                             precond=learned_act_fluents["precond"],
                                             add=learned_act_fluents["add"], delete=learned_act_fluents["delete"])
            # add learned_lifted action to all learned actions set
            self.learned_lifted_action.add(lifted_act)
        # initiate a learned fluent set
        self.make_learned_fluent_set()

    def generate_model(self) -> model.Model:
        self.loop_over_action_triplets()
        self.make_lifted_instances()
        return model.Model(self.learned_lifted_fluents, self.learned_lifted_action)

    # =======================================THE CLASS ============================================


class SAM:
    __sam_generator = None

    def __new__(cls, types: set[str] = None, trace_list: TraceList = None,
                action_2_sort: dict[str, list[str]] = None, sam_generator: SAMgenerator = None):
        """Creates a new SAM instance. if input includes sam_generator object than it uses the object provided
        instead of creating a new one
            Args:
                types (dict str -> str): a dic mapping each type to its super type, for example: [mazda, car].
                    means mazda type is type of car type
                trace_list(TraceList): an object holding a
                    list of traces from the same domain.
                action_2_sort(dict str -> list[str])

                                :return:
                                   a model based on SAM learning
                                """
        if sam_generator is not None:
            cls.__sam_generator = sam_generator
        else:
            cls.__sam_generator: SAMgenerator = SAMgenerator(types, trace_list, action_2_sort)

        return cls.__sam_generator.generate_model()
