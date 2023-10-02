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

    def test_model_extraction_1(self):
        generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True)
        generator.change_goal({
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
                ["package package4", "location city3-2"]
            ),
            get_fluent(
                "at",
                ["package package3", "location city6-1"]
            ),
            get_fluent(
                "at",
                ["package package2", "location city6-2"]
            ),
            get_fluent(
                "at",
                ["package package1", "location city2-1"]
            )
        })
        traces = [generator.generate_trace()]
        # prob 2
        generator = TraceFromGoal(problem_id=1496)
        generator.change_goal({
            get_fluent(
                "at",
                ["package obj31", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj22", "location apt2"]
            ),
            get_fluent(
                "at",
                ["package obj42", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj53", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj12", "location pos1"]
            ),
            get_fluent(
                "at",
                ["package obj32", "location apt1"]
            ),
            get_fluent(
                "at",
                ["package obj43", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj52", "location apt1"]
            ),
            get_fluent(
                "at",
                ["package obj51", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj21", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj11", "location pos3"]
            ),
            get_fluent(
                "at",
                ["package obj23", "location pos4"]
            ),
            get_fluent(
                "at",
                ["package obj33", "location pos3"]
            ),
            get_fluent(
                "at",
                ["package obj13", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj41", "location pos1"]
            )
        })
        traces.append(generator.generate_trace())

        trace_list: TraceList = TraceList(traces=traces)
        action_2_sort = {"load-truck": ["package", "truck", "location"],
                         "unload-truck": ["package", "truck", "location"],
                         "load-airplane": ["package", "airplane", "location "],
                         "unload-airplane": ["package", "airplane", "location "],
                         "drive-truck": ["truck", "location", "location", "city" ],
                         "fly-airplane":["airplane", "location", "location"]}
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(trace_list=trace_list, action_2_sort=action_2_sort)
        sam_model = sam_generator.generate_model()
        print(sam_model.details()+"\n")


    def test_model_extraction_2(self):
        pass
        # generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True)
        # generator.change_goal({
        #     get_fluent(
        #         "at",
        #         ["package package6", "location city1-2"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package package5", "location city6-2"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package package4", "location city3-2"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package package3", "location city6-1"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package package2", "location city6-2"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package package1", "location city2-1"]
        #     )
        # })
        # traces = [generator.generate_trace()]
        # # prob 2
        # generator = TraceFromGoal(problem_id=1496)
        # generator.change_goal({
        #     get_fluent(
        #         "at",
        #         ["package obj31", "location apt4"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj22", "location apt2"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj42", "location apt4"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj53", "location apt3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj12", "location pos1"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj32", "location apt1"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj43", "location apt3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj52", "location apt1"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj51", "location apt3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj21", "location apt4"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj11", "location pos3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj23", "location pos4"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj33", "location pos3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj13", "location apt3"]
        #     ),
        #     get_fluent(
        #         "at",
        #         ["package obj41", "location pos1"]
        #     )
        # })
        # traces.append(generator.generate_trace())
        #
        # trace_list: TraceList = TraceList(traces=traces)
        # action_2_sort = {"load-truck": ["package", "truck", "location"],
        #                  "unload-truck": ["package", "truck", "location"],
        #                  "load-airplane": ["package", "airplane", "location "],
        #                  "unload-airplane": ["package", "airplane", "location "],
        #                  "drive-truck": ["truck", "location", "location", "city" ],
        #                  "fly-airplane":["airplane", "location", "location"]}
        # sam_generator: sam.SAMgenerator = sam.SAMgenerator(trace_list=trace_list, action_2_sort=action_2_sort)
        # sam_model = sam_generator.generate_model()
        # print(sam_model.details()+"\n")