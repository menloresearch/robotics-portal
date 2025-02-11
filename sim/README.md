# Guide to a minimal set up of Unitree model in Genesis

To install the Genesis Embodied AI development library, follow these steps:

1. **Ensure Python 3.9 or Later is Installed**:
- Genesis requires Python version 3.9 or higher. You can verify your current Python version by running:
     ```bash
     python --version
     ```

2. **Install PyTorch**:
- Genesis depends on PyTorch. Follow the installation instructions specific to your system and requirements on the [PyTorch official website](https://pytorch.org/get-started/locally/).

3. **Install Genesis via PyPI**:
- Once Python and PyTorch are set up, install Genesis using pip:
     ```bash
     pip install genesis-world
     ```
- This command installs the latest stable release of Genesis from the Python Package Index (PyPI).

4. **Verify the Installation**:
- After installation, you can verify that Genesis is installed correctly by running a simple test script or checking the package version:
     ```bash
     python -c "import genesis; print(genesis.__version__)"
     ```
- This command should display the installed version of Genesis, confirming a successful installation.

5. **Cloning Unitree model repository**:
- To quickly load the robot model provided by Unitree, first clone the following repository in the same working folder as your `main.py`:
    > https://github.com/unitreerobotics/unitree_ros

    All the model is stored in the `robots/` path. You can choose between MuJoCo XML format or URDF. Genesis support both of them equally. 

6. **Loading the model into the environment**

The following is the minimal required code to render an interactive viewer of a Unitree model in Genesis. For MacOS, we need to spawn the sim on a different thread to be able to work with the interactive viewer, the example will be shown below this minimal code:

```python
import genesis as gs
import numpy as np

gs.init(
    backend=gs.gs_backend.gpu,
    precision="32",
)

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.MJCF(
        file="unitree_ros/robots/g1_description/g1_29dof_lock_waist_rev_1_0.xml",
    )
)

scene.build()

for i in range(200):
    scene.step()
```

Here is the required code for MacOS:

```python
import genesis as gs
import numpy as np

gs.init(
    backend=gs.gs_backend.metal,
    precision="32",
)

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.MJCF(
        file="unitree_ros/robots/g1_description/g1_29dof_lock_waist_rev_1_0.xml",
    )
)

scene.build()

def run_sim(scene):

    for i in range(200):
        scene.step()

gs.tools.run_in_another_thread(fn=run_sim, args=(scene,))

if scene.visualizer.viewer is not None:
    scene.visualizer.viewer.start()
```

7. **Run the simulation**
Just simply run the simulation by calling:

> python main.py

It is known that for more complex robots with more parts and joints, the interactive viewer tend to crash on Mac machine so in case it doesn't work, you should record the sim headlessly using a camera instead. You can learn how to do that in the Genesis visualization and rendering tutorial.
