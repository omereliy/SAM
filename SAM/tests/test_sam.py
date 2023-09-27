from unittest import TestCase

import macq.generate
from macq.trace import Action, Fluent, action, PlanningObject, State, SAS, TraceList, Trace
from macq.generate.pddl import Generator, TraceFromGoal
from macq.extract import model, LearnedLiftedFluent, LearnedLiftedAction

import sam


# !!!note to self: need to change goal fluents to the original goal(even if it set automatically)
# because an error accuses

def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1])
    for o in objs]
    return Fluent (name, objects)

class TestSAMgenerator(TestCase):
    generator: TraceFromGoal

    def setUp(self):
        self.generator = TraceFromGoal(problem_id=1481, observe_pres_effs=True)
        self.generator.change_goal({
            get_fluent(
                "at",
                ["package package6", "location city1-2"]
            ),
            get_fluent(
                "at",
                ["package package5", "location city6-2"]
            ),
            get_fluent(
                "at",
                ["package package4 ", "location city3-2"]
            ),
            get_fluent(
                "at",
                ["package package3 ", "location city6-1"]
            ),
            get_fluent(
                "at",
                ["package package2 ", "location city6-2"]
            ),
            get_fluent(
                "at",
                ["package package1 ", "location city2-1"]
            )
        })
        self.plan: macq.generate.Plan = self.generator.generate_plan()
        self.trace_list: TraceList = TraceList([self.generator.generate_trace()])


    def test_update_trace_list(self):
        # it works!!!!
        # self.trace_list.traces[0].print(view="actions")
        action_2_sort = {"load-truck": ["package", "truck", "location"],
                         "unload-truck": ["package", "truck", "location"],
                         "load-airplane": ["package", "airplane", "location "],
                         "unload-airplane": ["package", "airplane", "location "],
                         "drive-truck": ["truck", "location", "location", "city" ],
                         "fly-airplane":["airplane", "location", "location"]}
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(trace_list=self.trace_list, action_2_sort=action_2_sort)
        print(sam_generator.L_bLA)

    def test_update_l_b_la(self):
        self.fail()

    def test_update_action_2_sort(self):
        self.fail()

    def test_remove_redundant_preconditions(self):
        self.fail()

    def test_add_surely_effects(self):
        self.fail()

    def test_add_literal_binding_to_eff(self):
        self.fail()

    def test_loop_over_action_triplets(self):
        self.fail()

    def test_make_act_lifted_fluent_set(self):
        self.fail()

    def test_make_learned_fluent_set(self):
        self.fail()

    def test_make_lifted_instances(self):
        self.fail()

    def test_generate_model(self):
        self.fail()

    def test_make_act_sorts(self):
        pass
