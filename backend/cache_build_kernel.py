from scenes.go2.go2_sim import Go2Sim
from scenes.g1.g1_sim import G1Sim
from scenes.desk.desk_sim import BeatTheDeskSim
from app import default_config
import genesis as gs

gs.init()
scene = Go2Sim(config=default_config()["scenes"].get("go2", {}))
gs.destroy()
gs.init()
scene = G1Sim(config=default_config()["scenes"].get("g1", {}))
gs.destroy()
objects_stack = [
    {"red-cube": [0.4, 0.4, 0.5]},
    {"black-cube": [0.4, 0.7, 0.5]},
    {"green-cube": [0.7, 0.4, 0.5]},
    {"purple-cube": [0.7, 0.7, 0.5]},
]

objects_place = [
    {"red-cube": [0.4, 0.4, 0.5]},
    {"black-cube": [0.4, 0.7, 0.5]},
    {"green-container": [0.7, 0.7, 0.5]},
]
gs.init()
scene = BeatTheDeskSim(objects_stack)
gs.destroy()
gs.init()
scene = BeatTheDeskSim(objects_place)
gs.destroy()